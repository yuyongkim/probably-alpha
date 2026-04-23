"""Segment / Sum-of-the-Parts analysis.

DART's 사업보고서 XBRL carries a segment-revenue breakdown, but that data is
not yet ingested into ``financial_statements_db`` (which only holds income
statement + balance sheet line items). Until the segment extractor lands we
operate in a degraded mode:

    1. Identify holding-company / conglomerate candidates via universe metadata
       — names containing "홀딩스", "지주", "그룹" or a sector tag of "금융"
       with a large equity base.
    2. For each candidate compute a peer-median PBR *inside its primary
       sector* and multiply against book equity to get a single-segment SOTP
       proxy. A discount greater than 20% flags a *conglomerate discount*
       target.

This is deliberately a placeholder with a clear ``proxy=True`` flag on every
row — the UI can display a "Segment-level data pending" banner until the full
breakdown lands. The API shape already matches what the richer model will
return so no frontend churn is needed later.
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


def _load_universe_with_fundamentals(repo: Repository) -> list[dict[str, Any]]:
    """Join fnguide snapshots (for market-cap/pbr) onto the universe."""
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


def segment_scan(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Return candidate segment / SOTP plays with a proxy discount flag."""
    cache_key = "segment|sotp-proxy"
    if use_cache:
        hit = _CACHE.get(cache_key)
        if hit and time.time() - hit[0] <= _CACHE_TTL_SEC:
            return hit[1]

    repo = repo or Repository()
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
        # Implied sector-parity market cap
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
            }
        )

    out.sort(key=lambda r: r["discount"], reverse=True)

    if use_cache:
        _CACHE[cache_key] = (time.time(), out)
    return out


def segment_summary(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    rows = segment_scan(repo=repo, use_cache=use_cache)
    discounted = [r for r in rows if (r.get("discount") or 0) > 0.20]
    premium = [r for r in rows if (r.get("discount") or 0) < -0.20]
    kpi = {
        "candidates": len(rows),
        "discount_gt_20": len(discounted),
        "premium_gt_20": len(premium),
        "proxy_mode": True,
    }
    return {"kpi": kpi, "rows": rows[:50]}
