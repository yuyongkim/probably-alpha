"""Peer / comparables valuation — sector-level percentile ranking.

For every symbol with an fnguide snapshot we compute:

    - ``per_rank_pct``  — percentile of PER inside the symbol's sector (0=
                           cheapest, 1=most expensive).
    - ``pbr_rank_pct``  — same for PBR.
    - ``per_vs_median`` — (per / sector_median_per − 1); negative = cheaper.

Outliers are flagged when both PER and PBR land in the bottom quartile of the
sector AND the symbol has a positive ROE — that's the "cheap & profitable"
combo value investors hunt for.

One SQL query + one JSON parse per symbol. Sub-second for 2.5k cached
snapshots. Cached 1h.
"""
from __future__ import annotations

import json
import logging
import statistics
import time
from collections import defaultdict
from typing import Any

from sqlalchemy import text

from ky_core.storage import Repository

log = logging.getLogger(__name__)

_CACHE_TTL_SEC = 3600.0
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def _percentile(values: list[float], target: float) -> float:
    """Fraction of ``values`` strictly less than ``target`` (0..1)."""
    if not values:
        return 0.5
    under = sum(1 for v in values if v < target)
    return under / len(values)


def _load_universe(repo: Repository) -> list[dict[str, Any]]:
    q = text(
        """
        SELECT f.symbol, f.payload, u.name, u.sector, u.market
        FROM fnguide_snapshots f
        LEFT JOIN universe u
               ON u.ticker = f.symbol
              AND u.owner_id = f.owner_id
        WHERE f.owner_id = :oid
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()

    out: list[dict[str, Any]] = []
    for sym, payload_json, name, sector, market in rows:
        if not sector or not payload_json:
            continue
        try:
            p = json.loads(payload_json)
        except Exception:  # noqa: BLE001
            continue
        per = p.get("per")
        pbr = p.get("pbr")
        roe = p.get("roe")
        if per is None and pbr is None:
            continue
        out.append(
            {
                "symbol": sym,
                "name": name,
                "sector": sector,
                "market": market,
                "per": float(per) if per is not None else None,
                "pbr": float(pbr) if pbr is not None else None,
                "roe": float(roe) if roe is not None else None,
                "dividend_yield": p.get("dividend_yield"),
                "market_cap": p.get("market_cap") or p.get("market_cap_raw"),
            }
        )
    return out


def comparables_scan(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    if use_cache:
        hit = _CACHE.get("comparables")
        if hit and time.time() - hit[0] <= _CACHE_TTL_SEC:
            return hit[1]

    repo = repo or Repository()
    rows = _load_universe(repo)

    # Bucket by sector and gather per/pbr samples.
    per_buckets: dict[str, list[float]] = defaultdict(list)
    pbr_buckets: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r.get("per") is not None and r["per"] > 0:
            per_buckets[r["sector"]].append(r["per"])
        if r.get("pbr") is not None and r["pbr"] > 0:
            pbr_buckets[r["sector"]].append(r["pbr"])

    median_per = {s: statistics.median(v) for s, v in per_buckets.items() if len(v) >= 5}
    median_pbr = {s: statistics.median(v) for s, v in pbr_buckets.items() if len(v) >= 5}

    out: list[dict[str, Any]] = []
    for r in rows:
        sector = r["sector"]
        per_vals = per_buckets.get(sector, [])
        pbr_vals = pbr_buckets.get(sector, [])
        # Require at least 5 peers in the sector for a meaningful rank.
        if len(per_vals) + len(pbr_vals) < 10:
            continue
        per = r.get("per") if r.get("per") and r["per"] > 0 else None
        pbr = r.get("pbr") if r.get("pbr") and r["pbr"] > 0 else None
        per_pct = _percentile(per_vals, per) if per is not None else None
        pbr_pct = _percentile(pbr_vals, pbr) if pbr is not None else None
        sec_med_per = median_per.get(sector)
        sec_med_pbr = median_pbr.get(sector)
        per_vs_median = (per / sec_med_per - 1) if per is not None and sec_med_per else None
        pbr_vs_median = (pbr / sec_med_pbr - 1) if pbr is not None and sec_med_pbr else None
        outlier_cheap = bool(
            per_pct is not None and pbr_pct is not None
            and per_pct <= 0.25 and pbr_pct <= 0.25
            and (r.get("roe") or 0) > 5
        )
        out.append(
            {
                **r,
                "sector_peer_count": max(len(per_vals), len(pbr_vals)),
                "per_rank_pct": per_pct,
                "pbr_rank_pct": pbr_pct,
                "sector_median_per": sec_med_per,
                "sector_median_pbr": sec_med_pbr,
                "per_vs_median": per_vs_median,
                "pbr_vs_median": pbr_vs_median,
                "outlier_cheap": outlier_cheap,
            }
        )

    # Default sort: cheapest outliers first.
    out.sort(
        key=lambda r: (
            -int(r.get("outlier_cheap", False)),
            (r.get("per_rank_pct") if r.get("per_rank_pct") is not None else 1.0),
        )
    )
    if use_cache:
        _CACHE["comparables"] = (time.time(), out)
    return out


def comparables_by_sector(
    sector: str,
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    rows = comparables_scan(repo=repo, use_cache=use_cache)
    return [r for r in rows if r["sector"] == sector]


def comparables_summary(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    rows = comparables_scan(repo=repo, use_cache=use_cache)
    outliers = [r for r in rows if r.get("outlier_cheap")]
    sector_counts: dict[str, int] = defaultdict(int)
    for r in rows:
        sector_counts[r["sector"]] += 1
    top_sectors = sorted(sector_counts.items(), key=lambda t: -t[1])[:10]
    kpi = {
        "ranked": len(rows),
        "outlier_cheap": len(outliers),
        "sectors_covered": len(sector_counts),
    }
    return {
        "kpi": kpi,
        "outliers": outliers[:30],
        "rows": rows[:50],
        "top_sectors": [{"sector": s, "count": c} for s, c in top_sectors],
    }
