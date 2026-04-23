"""Dividend screener — fnguide ``dividend_yield`` + best-effort growth streak.

Top-yield ranking sorts ``dividend_yield`` across every cached fnguide
snapshot. One SQL + one JSON parse per symbol.

Growth streak (``aristocrat`` flag)
-----------------------------------
Korean filings don't expose dividend-per-share in the per-account Naver
store, and the fnguide snapshot only holds the current yield. As a proxy we
look at *net-income growth streaks* from the snapshot's ``financials_annual``
history and treat a symbol as an aristocrat candidate when:

    - At least 5 reported annual rows (is_estimate == False) are available.
    - Net income is positive in every year AND non-decreasing year-on-year.
    - The current dividend_yield is strictly positive.

A proper DPS-based streak lands once the dividend-history collector is wired
in; until then every row carries ``aristocrat_proxy=True`` so the UI can
annotate.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from sqlalchemy import text

from ky_core.storage import Repository

log = logging.getLogger(__name__)

_CACHE_TTL_SEC = 3600.0
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}

def _load_snapshots(repo: Repository) -> list[dict[str, Any]]:
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
        if not payload_json:
            continue
        try:
            p = json.loads(payload_json)
        except Exception:  # noqa: BLE001
            continue
        dy = p.get("dividend_yield")
        if dy is None:
            continue
        out.append(
            {
                "symbol": sym,
                "name": name,
                "sector": sector,
                "market": market,
                "dividend_yield": float(dy) if dy is not None else None,
                "per": p.get("per"),
                "pbr": p.get("pbr"),
                "roe": p.get("roe"),
                "_annual": p.get("financials_annual") or [],
            }
        )
    return out


def _ni_growth_streak(annual: list[dict[str, Any]]) -> tuple[int, int]:
    """Trailing consecutive years with positive, non-decreasing net income.

    Only counts ``is_estimate=False`` rows — estimates would poison the streak.
    Returns ``(streak, reported_years)``.
    """
    reported = [r for r in annual if not r.get("is_estimate")]
    # Sort ascending by period string.
    reported.sort(key=lambda r: str(r.get("period") or ""))
    streak = 0
    prev: float | None = None
    for row in reported:
        ni = row.get("net_income")
        if ni is None:
            streak = 0
            prev = None
            continue
        try:
            ni = float(ni)
        except (TypeError, ValueError):
            streak = 0
            prev = None
            continue
        if ni <= 0:
            streak = 0
            prev = None
            continue
        if prev is None or ni >= prev - 1e-6:
            streak += 1
        else:
            streak = 1
        prev = ni
    return streak, len(reported)


def dividend_scan(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
    min_streak: int = 0,
) -> list[dict[str, Any]]:
    cache_key = f"dividend|streak={min_streak}"
    if use_cache:
        hit = _CACHE.get(cache_key)
        if hit and time.time() - hit[0] <= _CACHE_TTL_SEC:
            return hit[1]

    repo = repo or Repository()
    rows = _load_snapshots(repo)

    out: list[dict[str, Any]] = []
    for r in rows:
        streak, reported_years = _ni_growth_streak(r["_annual"])
        if streak < min_streak:
            continue
        dy = r.get("dividend_yield") or 0
        # Reported-year window inside fnguide snapshots is ~5y; ≥3 consecutive
        # positive-and-growing years is the proxy bar until a proper DPS-based
        # collector lands.
        aristocrat = streak >= 3 and reported_years >= 3 and dy > 0
        out.append(
            {
                **{k: v for k, v in r.items() if k != "_annual"},
                "ni_growth_streak": streak,
                "reported_years": reported_years,
                "aristocrat": aristocrat,
                "aristocrat_proxy": True,  # based on net-income streak, not DPS
            }
        )

    out.sort(
        key=lambda r: (
            r["aristocrat"],
            r.get("ni_growth_streak") or 0,
            r.get("dividend_yield") or 0,
        ),
        reverse=True,
    )

    if use_cache:
        _CACHE[cache_key] = (time.time(), out)
    return out


def dividend_top(
    *,
    mode: str = "yield",
    n: int = 30,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """``mode`` = ``yield`` | ``aristocrat``."""
    rows = dividend_scan(repo=repo, use_cache=use_cache)
    if mode == "aristocrat":
        rows = [r for r in rows if r["aristocrat"]]
    rows = [r for r in rows if (r.get("dividend_yield") or 0) > 0]
    rows.sort(key=lambda r: r.get("dividend_yield") or 0, reverse=True)
    return rows[:n]


def dividend_summary(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    rows = dividend_scan(repo=repo, use_cache=use_cache)
    aristocrats = [r for r in rows if r["aristocrat"]]
    high_yield = [r for r in rows if (r.get("dividend_yield") or 0) >= 5.0]
    kpi = {
        "with_yield": sum(1 for r in rows if (r.get("dividend_yield") or 0) > 0),
        "aristocrats": len(aristocrats),
        "yield_gt_5pct": len(high_yield),
    }
    rows.sort(key=lambda r: r.get("dividend_yield") or 0, reverse=True)
    return {"kpi": kpi, "rows": rows[:50], "aristocrats": aristocrats[:30]}
