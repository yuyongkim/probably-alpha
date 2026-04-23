"""Segment / Sum-of-the-Parts analysis.

Two data paths, chosen per-symbol at evaluation time:

1. **Real**: if ``financial_segments`` has rows for the symbol (scraped from
   DART 사업보고서), we surface the actual segment breakdown — segment name +
   revenue + share. This is the authoritative view and what the UI's "사업부
   별 매출" visualisation consumes.
2. **Proxy**: if no DART segments are persisted yet (the scraper is best-
   effort and only runs against a subset of the universe), we fall back to
   the legacy sector-parity PBR proxy to at least flag conglomerate-discount
   candidates. Rows from this path carry ``source="proxy:pbr"``.

Both paths emit the same row schema so the Frontend can render one table and
switch styling only on ``source``.
"""
from __future__ import annotations

import json
import logging
import statistics
import time
from typing import Any

from sqlalchemy import text

from ky_core.storage import Repository

log = logging.getLogger(__name__)

_CACHE_TTL_SEC = 3600.0
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}

HOLDING_TOKENS = ("홀딩스", "지주", "그룹")


# --------------------------------------------------------------------------- #
# DART-sourced segments                                                       #
# --------------------------------------------------------------------------- #


def _load_dart_segments(repo: Repository) -> list[dict[str, Any]]:
    """Return every persisted segment row joined to universe/fnguide.

    The segments table stores one row per (symbol, period, segment). We only
    surface the *latest* ``period_end`` per symbol — older years exist but
    belong to a historical view we haven't built yet.
    """
    q = text(
        """
        SELECT fs.symbol,
               fs.period_end,
               fs.segment_name,
               fs.revenue,
               fs.operating_income,
               fs.revenue_share,
               u.name AS company_name,
               u.sector,
               u.market,
               f.payload
        FROM financial_segments fs
        LEFT JOIN universe u
               ON u.ticker = fs.symbol
              AND u.owner_id = fs.owner_id
        LEFT JOIN fnguide_snapshots f
               ON f.symbol = fs.symbol
              AND f.owner_id = fs.owner_id
        WHERE fs.owner_id = :oid
          AND fs.period_end = (
              SELECT MAX(fs2.period_end)
                FROM financial_segments fs2
               WHERE fs2.symbol = fs.symbol
                 AND fs2.owner_id = fs.owner_id
          )
        ORDER BY fs.symbol, fs.revenue_share DESC NULLS LAST, fs.revenue DESC
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()

    grouped: dict[str, dict[str, Any]] = {}
    for sym, period_end, seg_name, revenue, op_inc, share, coname, sector, market, payload_json in rows:
        payload: dict[str, Any] = {}
        if payload_json:
            try:
                payload = json.loads(payload_json)
            except Exception:  # noqa: BLE001
                payload = {}
        ent = grouped.setdefault(
            sym,
            {
                "symbol": sym,
                "name": coname,
                "sector": sector,
                "market": market,
                "period_end": period_end,
                "market_cap": payload.get("market_cap") or payload.get("market_cap_raw"),
                "segments": [],
                "source": "dart",
            },
        )
        ent["segments"].append(
            {
                "segment_name": seg_name,
                "revenue": revenue,
                "operating_income": op_inc,
                "revenue_share": share,
            }
        )
    return list(grouped.values())


def _summarise_dart(row: dict[str, Any]) -> dict[str, Any]:
    """Compute a top-segment concentration metric per company. The frontend
    already knows what to do with ``segments`` but the summary table needs a
    single numeric column — use the largest segment's share."""
    segs = row["segments"]
    top = max(segs, key=lambda s: (s.get("revenue_share") or 0)) if segs else None
    top_share = top.get("revenue_share") if top else None
    top_name = top.get("segment_name") if top else None
    return {
        **row,
        "segment_count": len(segs),
        "top_segment": top_name,
        "top_segment_share": top_share,
    }


# --------------------------------------------------------------------------- #
# Proxy: sector-parity PBR (unchanged behaviour from the pre-DART build)      #
# --------------------------------------------------------------------------- #


def _load_universe_with_fundamentals(repo: Repository) -> list[dict[str, Any]]:
    q = text(
        """
        SELECT u.ticker, u.name, u.sector, u.market, f.payload
        FROM universe u
        LEFT JOIN fnguide_snapshots f
               ON f.symbol = u.ticker
              AND f.owner_id = u.owner_id
        WHERE u.owner_id = :oid
          AND u.market IN ('KOSPI', 'KOSDAQ', 'KONEX')
          AND u.is_etf = 0
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()

    out: list[dict[str, Any]] = []
    for ticker, name, sector, market, payload_json in rows:
        payload: dict[str, Any] = {}
        if payload_json:
            try:
                payload = json.loads(payload_json)
            except Exception:  # noqa: BLE001
                payload = {}
        out.append(
            {
                "symbol": ticker,
                "name": name,
                "sector": sector,
                "market": market,
                "pbr": payload.get("pbr"),
                "per": payload.get("per"),
                "bps": payload.get("bps"),
                "market_cap": payload.get("market_cap") or payload.get("market_cap_raw"),
            }
        )
    return out


def _sector_median_pbr(rows: list[dict[str, Any]]) -> dict[str, float]:
    buckets: dict[str, list[float]] = {}
    for r in rows:
        if r.get("sector") and r.get("pbr") is not None and r["pbr"] > 0:
            buckets.setdefault(r["sector"], []).append(float(r["pbr"]))
    return {
        sector: statistics.median(vals)
        for sector, vals in buckets.items()
        if len(vals) >= 5
    }


def _is_holding_candidate(row: dict[str, Any]) -> bool:
    name = row.get("name") or ""
    sector = (row.get("sector") or "").strip()
    if any(tok in name for tok in HOLDING_TOKENS):
        return True
    mcap = row.get("market_cap")
    if isinstance(mcap, (int, float)) and mcap > 1e12 and sector == "금융":
        return True
    return False


def _proxy_rows(repo: Repository) -> list[dict[str, Any]]:
    rows = _load_universe_with_fundamentals(repo)
    sector_median = _sector_median_pbr(rows)

    out: list[dict[str, Any]] = []
    for r in rows:
        if not _is_holding_candidate(r):
            continue
        mcap = r.get("market_cap")
        pbr = r.get("pbr")
        sector = r.get("sector")
        if not isinstance(mcap, (int, float)) or not pbr or not sector or pbr <= 0:
            continue
        median_pbr = sector_median.get(sector)
        if median_pbr is None or median_pbr <= 0:
            continue
        sotp_proxy = float(mcap) * (median_pbr / pbr)
        discount = (sotp_proxy - mcap) / sotp_proxy if sotp_proxy > 0 else None
        if discount is None:
            continue
        out.append(
            {
                "symbol": r["symbol"],
                "name": r["name"],
                "sector": sector,
                "market": r["market"],
                "market_cap": mcap,
                "sotp_proxy": sotp_proxy,
                "discount": discount,
                "pbr": pbr,
                "sector_median_pbr": median_pbr,
                "proxy": True,
                "source": "proxy:pbr",
            }
        )
    out.sort(key=lambda r: r["discount"], reverse=True)
    return out


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def segment_scan(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Return segment + SOTP-proxy candidates.

    Real DART-sourced rows come first (sorted by company size when known);
    PBR-proxy rows are appended for holdings with no DART coverage yet.
    """
    cache_key = "segment|unified"
    if use_cache:
        hit = _CACHE.get(cache_key)
        if hit and time.time() - hit[0] <= _CACHE_TTL_SEC:
            return hit[1]

    repo = repo or Repository()

    dart_rows_raw = _load_dart_segments(repo)
    dart_rows = [_summarise_dart(r) for r in dart_rows_raw]
    dart_rows.sort(
        key=lambda r: (r.get("market_cap") or 0),
        reverse=True,
    )
    dart_symbols = {r["symbol"] for r in dart_rows}

    proxy_rows = [r for r in _proxy_rows(repo) if r["symbol"] not in dart_symbols]

    out = dart_rows + proxy_rows
    if use_cache:
        _CACHE[cache_key] = (time.time(), out)
    return out


def segment_summary(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    rows = segment_scan(repo=repo, use_cache=use_cache)
    dart_rows = [r for r in rows if r.get("source") == "dart"]
    proxy_rows = [r for r in rows if r.get("source") == "proxy:pbr"]
    discounted = [r for r in proxy_rows if (r.get("discount") or 0) > 0.20]
    premium = [r for r in proxy_rows if (r.get("discount") or 0) < -0.20]
    kpi = {
        "candidates": len(rows),
        "dart_covered": len(dart_rows),
        "proxy_covered": len(proxy_rows),
        "discount_gt_20": len(discounted),
        "premium_gt_20": len(premium),
        "proxy_mode": len(dart_rows) == 0,
    }
    # Cap rows we return over the wire.
    return {"kpi": kpi, "rows": rows[:80]}
