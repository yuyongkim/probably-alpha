"""Naver / FnGuide snapshot client.

Two endpoints, one public surface.

Primary (JSON, stable):
    GET https://m.stock.naver.com/api/stock/{symbol}/integration

Fallback (HTML, ugly but comprehensive):
    GET https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?
        pGB=1&gicode=A{symbol}&cID=&MenuYn=Y&ReportGB=&NewMenuID=11&stkGb=701

Policy:
  * 10 minute per-symbol cache (caller supplies repository).
  * Polite: single request/request/symbol; desktop UA; no parallel fetches.
  * Silent on fallback — if either source fails the adapter returns
    whatever partial data it collected with ``degraded=True`` set.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from ky_adapters.base import AdapterError, BaseAdapter
from ky_adapters.naver_fnguide.parser import (
    is_valid_symbol,
    parse_fnguide_html,
    parse_naver_integration,
)

logger = logging.getLogger(__name__)

NAVER_URL = "https://m.stock.naver.com/api/stock/{symbol}/integration"
FNGUIDE_URL = (
    "https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp"
    "?pGB=1&gicode=A{symbol}&cID=&MenuYn=Y&ReportGB=&NewMenuID=11&stkGb=701"
)

# Browser-ish UA avoids the trivial bot blocks; we do not impersonate anyone
# particular and stay well under any plausible rate limit.
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


@dataclass
class FnguideSnapshot:
    """Normalised fundamentals snapshot."""

    symbol: str
    fetched_at: float                       # unix seconds
    source: str                              # "naver_mobile" | "fnguide" | "mixed"
    degraded: bool = False
    target_price: float | None = None
    investment_opinion: str | None = None
    per: float | None = None
    pbr: float | None = None
    eps: float | None = None
    bps: float | None = None
    roe: float | None = None
    roa: float | None = None
    debt_ratio: float | None = None
    dividend_yield: float | None = None
    market_cap: float | None = None
    foreign_ratio: float | None = None
    major_shareholder_name: str | None = None
    major_shareholder_pct: float | None = None
    financials_quarterly: list[dict[str, Any]] = field(default_factory=list)
    financials_annual: list[dict[str, Any]] = field(default_factory=list)
    peers: list[dict[str, Any]] = field(default_factory=list)
    summary_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "fetched_at": self.fetched_at,
            "source": self.source,
            "degraded": self.degraded,
            "target_price": self.target_price,
            "investment_opinion": self.investment_opinion,
            "per": self.per,
            "pbr": self.pbr,
            "eps": self.eps,
            "bps": self.bps,
            "roe": self.roe,
            "roa": self.roa,
            "debt_ratio": self.debt_ratio,
            "dividend_yield": self.dividend_yield,
            "market_cap": self.market_cap,
            "foreign_ratio": self.foreign_ratio,
            "major_shareholder_name": self.major_shareholder_name,
            "major_shareholder_pct": self.major_shareholder_pct,
            "financials_quarterly": self.financials_quarterly,
            "financials_annual": self.financials_annual,
            "peers": self.peers,
            "summary_notes": self.summary_notes,
        }


# --------------------------------------------------------------------------- #
# Adapter                                                                      #
# --------------------------------------------------------------------------- #


class FnguideAdapter(BaseAdapter):
    """Combined Naver+FnGuide snapshot fetcher."""

    source_id = "naver_fnguide"
    priority = 5

    def __init__(self, *, client: httpx.Client | None = None) -> None:
        super().__init__(client=client)

    @classmethod
    def from_settings(cls) -> "FnguideAdapter":
        return cls()

    # --------- Contract ---------

    def healthcheck(self) -> dict[str, Any]:
        t0 = time.perf_counter()
        try:
            resp = self._request(
                "GET",
                NAVER_URL.format(symbol="005930"),
                headers={"User-Agent": UA, "Referer": "https://m.stock.naver.com/"},
                timeout=5.0,
                retries=1,
            )
            if resp.status_code != 200:
                return self._timed_fail(self.source_id, f"naver HTTP {resp.status_code}")
        except Exception as exc:  # noqa: BLE001
            return self._timed_fail(self.source_id, str(exc))
        return self._timed_ok(
            (time.perf_counter() - t0) * 1000,
            self.source_id,
            {"probe": "naver_integration"},
        )

    # --------- Public surface ---------

    def get_snapshot(self, symbol: str) -> FnguideSnapshot:
        if not is_valid_symbol(symbol):
            raise AdapterError(f"invalid KRX symbol: {symbol!r}")

        primary = self._try_naver(symbol)
        if primary and _covers_core(primary):
            return _as_snapshot(symbol, primary, source="naver_mobile")

        fallback = self._try_fnguide(symbol)
        if primary and fallback:
            merged = _merge(primary, fallback)
            return _as_snapshot(symbol, merged, source="mixed")
        if primary:
            return _as_snapshot(symbol, primary, source="naver_mobile", degraded=True)
        if fallback:
            return _as_snapshot(symbol, fallback, source="fnguide", degraded=True)

        # Neither source answered — return an empty stub with degraded flag.
        logger.warning("fnguide: both naver and fnguide failed for %s", symbol)
        return FnguideSnapshot(
            symbol=symbol,
            fetched_at=time.time(),
            source="none",
            degraded=True,
            summary_notes=["no snapshot sources available"],
        )

    # --------- Fetchers ---------

    def _try_naver(self, symbol: str) -> dict[str, Any] | None:
        try:
            resp = self._request(
                "GET",
                NAVER_URL.format(symbol=symbol),
                headers={
                    "User-Agent": UA,
                    "Referer": "https://m.stock.naver.com/",
                    "Accept": "application/json",
                },
                timeout=6.0,
                retries=1,
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("fnguide: naver fetch failed for %s: %s", symbol, exc)
            return None
        if resp.status_code != 200:
            logger.info("fnguide: naver HTTP %s for %s", resp.status_code, symbol)
            return None
        try:
            payload = resp.json()
        except ValueError:
            logger.info("fnguide: naver non-json for %s", symbol)
            return None
        try:
            return parse_naver_integration(payload)
        except Exception:  # noqa: BLE001
            logger.exception("fnguide: naver parse failed for %s", symbol)
            return None

    def _try_fnguide(self, symbol: str) -> dict[str, Any] | None:
        try:
            resp = self._request(
                "GET",
                FNGUIDE_URL.format(symbol=symbol),
                headers={
                    "User-Agent": UA,
                    "Referer": "https://comp.fnguide.com/",
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=8.0,
                retries=1,
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("fnguide: fnguide fetch failed for %s: %s", symbol, exc)
            return None
        if resp.status_code != 200:
            logger.info("fnguide: fnguide HTTP %s for %s", resp.status_code, symbol)
            return None
        try:
            return parse_fnguide_html(resp.text)
        except Exception:  # noqa: BLE001
            logger.exception("fnguide: fnguide parse failed for %s", symbol)
            return None


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


_CORE_FIELDS = ("per", "pbr", "eps", "roe")


def _covers_core(d: dict[str, Any]) -> bool:
    return sum(1 for k in _CORE_FIELDS if d.get(k) is not None) >= 2


def _merge(primary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    out = dict(primary)
    for k, v in fallback.items():
        if k in ("summary_notes", "peers", "financials_quarterly", "financials_annual"):
            current = out.get(k) or []
            if not current and v:
                out[k] = v
            continue
        if out.get(k) is None and v is not None:
            out[k] = v
    return out


def _as_snapshot(
    symbol: str,
    data: dict[str, Any],
    *,
    source: str,
    degraded: bool = False,
) -> FnguideSnapshot:
    return FnguideSnapshot(
        symbol=symbol,
        fetched_at=time.time(),
        source=source,
        degraded=degraded,
        target_price=data.get("target_price"),
        investment_opinion=data.get("investment_opinion"),
        per=data.get("per"),
        pbr=data.get("pbr"),
        eps=data.get("eps"),
        bps=data.get("bps"),
        roe=data.get("roe"),
        roa=data.get("roa"),
        debt_ratio=data.get("debt_ratio"),
        dividend_yield=data.get("dividend_yield"),
        market_cap=data.get("market_cap"),
        foreign_ratio=data.get("foreign_ratio"),
        major_shareholder_name=data.get("major_shareholder_name"),
        major_shareholder_pct=data.get("major_shareholder_pct"),
        financials_quarterly=data.get("financials_quarterly") or [],
        financials_annual=data.get("financials_annual") or [],
        peers=data.get("peers") or [],
        summary_notes=data.get("summary_notes") or [],
    )
