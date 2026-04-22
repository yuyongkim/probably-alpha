"""EXIM (Korea Eximbank) exchange rate adapter.

Endpoint:
  https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON
Query:
  ?authkey=...&searchdate=YYYYMMDD&data=AP01

Note: the Eximbank only publishes on business days and serves the most recent
available rate. Querying a weekend/holiday returns an empty list — callers
should fall back to the prior business day.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from ky_adapters.base import AdapterError, AuthError, BaseAdapter

EXIM_BASE = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"


@dataclass
class EXIMRate:
    cur_unit: str  # e.g. USD, JPY(100), CNH
    cur_nm: str
    deal_bas_r: float | None  # 매매기준율
    ttb: float | None  # 전신환 매입률
    tts: float | None  # 전신환 매도율
    as_of: str  # ISO YYYY-MM-DD

    def as_row(self, source_id: str = "exim") -> dict[str, Any]:
        series_id = f"fx/{self.cur_unit}/deal_bas_r"
        return {
            "source_id": source_id,
            "series_id": series_id,
            "date": self.as_of,
            "value": self.deal_bas_r,
            "unit": "KRW per unit",
        }


class EXIMAdapter(BaseAdapter):
    source_id = "exim"
    priority = 2

    def __init__(self, auth_key: Optional[str] = None, base_url: str = EXIM_BASE) -> None:
        super().__init__()
        self.auth_key = auth_key
        self.base_url = base_url

    @classmethod
    def from_settings(cls) -> "EXIMAdapter":
        return cls(auth_key=cls._env("EXIM_API_KEY"))

    # --------- Contract ---------

    def healthcheck(self) -> dict[str, Any]:
        if not self.auth_key:
            return self._timed_fail(self.source_id, "EXIM_API_KEY not configured")
        t0 = time.perf_counter()
        try:
            rates = self.get_rates()
            # Eximbank returns [] on weekends — reachable even when empty.
            ok = isinstance(rates, list)
        except Exception as exc:  # noqa: BLE001
            return self._timed_fail(self.source_id, str(exc))
        latency_ms = (time.perf_counter() - t0) * 1000
        return self._timed_ok(latency_ms, self.source_id, {"api_ok": ok, "rows": len(rates)})

    # --------- API surface ---------

    def get_rates(
        self,
        search_date: date | str | None = None,
        data: str = "AP01",
    ) -> list[EXIMRate]:
        """Fetch FX rates. ``data=AP01`` is the standard FX feed."""
        if not self.auth_key:
            raise AuthError("EXIM_API_KEY not configured")
        iso = _eximdate(search_date) if search_date else ""
        params: dict[str, Any] = {"authkey": self.auth_key, "data": data}
        if iso:
            params["searchdate"] = iso
        resp = self._request("GET", self.base_url, params=params)
        if resp.status_code != 200:
            raise AdapterError(f"EXIM → HTTP {resp.status_code}: {resp.text[:200]}")
        try:
            body = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise AdapterError(f"EXIM: invalid JSON: {exc}") from exc
        if not isinstance(body, list):
            # error envelope: {"result": 2, ...}
            if isinstance(body, dict) and "result" in body and body["result"] != 1:
                raise AdapterError(f"EXIM result={body.get('result')}")
            return []
        iso_out = _iso_from_eximdate(iso) if iso else date.today().isoformat()
        out: list[EXIMRate] = []
        for row in body:
            out.append(
                EXIMRate(
                    cur_unit=row.get("cur_unit", ""),
                    cur_nm=row.get("cur_nm", ""),
                    deal_bas_r=_parse_num(row.get("deal_bas_r")),
                    ttb=_parse_num(row.get("ttb")),
                    tts=_parse_num(row.get("tts")),
                    as_of=iso_out,
                )
            )
        return out


def _parse_num(val: Any) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", ""))
    except ValueError:
        return None


def _eximdate(d: date | str) -> str:
    if isinstance(d, date):
        return d.strftime("%Y%m%d")
    raw = str(d).replace("-", "")
    return raw


def _iso_from_eximdate(yyyymmdd: str) -> str:
    if len(yyyymmdd) == 8 and yyyymmdd.isdigit():
        return f"{yyyymmdd[0:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
    return yyyymmdd
