"""Dividend screener — combined DART DPS history + fnguide snapshot.

Aristocrat detection has two evaluation paths:

1. **Real (preferred)** — when ``dividend_history`` rows are available for a
   symbol, compute a proper *DPS growth streak*: consecutive fiscal years
   with positive, non-decreasing dividend-per-share. 10 years is the target
   aristocrat bar but we emit a configurable minimum.
2. **Proxy (fallback)** — when there is no DART DPS row, fall back to the
   old net-income growth streak sourced from the fnguide snapshot's
   ``financials_annual`` list. These rows carry ``aristocrat_proxy=True``.

Top-yield ranking remains sourced from fnguide ``dividend_yield``.
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

# Calendar years of consecutive DPS growth that earn the "aristocrat" badge.
ARISTOCRAT_YEARS_REAL = 10   # DART-backed
ARISTOCRAT_YEARS_PROXY = 3   # net-income fallback


# --------------------------------------------------------------------------- #
# Data loading                                                                #
# --------------------------------------------------------------------------- #


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


def _load_dps_history(repo: Repository) -> dict[str, list[dict[str, Any]]]:
    """Return a ``{symbol: [{period_end, dps}, …]}`` map sorted ascending."""
    rows = repo.get_all_dividend_history()
    by_sym: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        if r.get("dps") is None:
            continue
        by_sym.setdefault(r["symbol"], []).append(r)
    # Already ordered ASC by (symbol, period_end) in the repo query, but be
    # defensive in case we ever relax that.
    for sym, lst in by_sym.items():
        lst.sort(key=lambda x: x.get("period_end") or "")
    return by_sym


# --------------------------------------------------------------------------- #
# Streak computation                                                          #
# --------------------------------------------------------------------------- #


def _dps_growth_streak(history: list[dict[str, Any]]) -> tuple[int, int]:
    """Consecutive trailing years with positive, non-decreasing DPS.

    Returns ``(streak, reported_years)``.
    """
    streak = 0
    prev: float | None = None
    reported = 0
    for row in history:
        dps = row.get("dps")
        if dps is None:
            streak = 0
            prev = None
            continue
        try:
            v = float(dps)
        except (TypeError, ValueError):
            streak = 0
            prev = None
            continue
        reported += 1
        if v <= 0:
            streak = 0
            prev = None
            continue
        if prev is None or v >= prev - 1e-6:
            streak += 1
        else:
            streak = 1
        prev = v
    return streak, reported


def _ni_growth_streak(annual: list[dict[str, Any]]) -> tuple[int, int]:
    """Fallback net-income streak (original proxy behaviour)."""
    reported = [r for r in annual if not r.get("is_estimate")]
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


# --------------------------------------------------------------------------- #
# Public                                                                      #
# --------------------------------------------------------------------------- #


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
    snapshots = _load_snapshots(repo)
    dps_history = _load_dps_history(repo)

    out: list[dict[str, Any]] = []
    for r in snapshots:
        sym = r["symbol"]
        dy = r.get("dividend_yield") or 0

        history = dps_history.get(sym)
        if history:
            streak, reported_years = _dps_growth_streak(history)
            aristocrat = (
                streak >= ARISTOCRAT_YEARS_REAL
                and reported_years >= ARISTOCRAT_YEARS_REAL
                and dy > 0
            )
            source = "dart"
            proxy_flag = False
            latest_dps = history[-1].get("dps") if history else None
        else:
            streak, reported_years = _ni_growth_streak(r["_annual"])
            aristocrat = (
                streak >= ARISTOCRAT_YEARS_PROXY
                and reported_years >= ARISTOCRAT_YEARS_PROXY
                and dy > 0
            )
            source = "proxy:ni"
            proxy_flag = True
            latest_dps = None

        if streak < min_streak:
            continue

        out.append(
            {
                **{k: v for k, v in r.items() if k != "_annual"},
                "dps_streak": streak if not proxy_flag else None,
                "ni_growth_streak": streak,   # preserved for back-compat
                "reported_years": reported_years,
                "latest_dps": latest_dps,
                "aristocrat": aristocrat,
                "aristocrat_proxy": proxy_flag,
                "source": source,
            }
        )

    out.sort(
        key=lambda r: (
            # Real aristocrats first, then by streak depth, then by yield.
            (r["aristocrat"] and not r["aristocrat_proxy"]),
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
    real_aristocrats = [r for r in aristocrats if not r["aristocrat_proxy"]]
    high_yield = [r for r in rows if (r.get("dividend_yield") or 0) >= 5.0]
    dart_covered = sum(1 for r in rows if r.get("source") == "dart")
    kpi = {
        "with_yield": sum(1 for r in rows if (r.get("dividend_yield") or 0) > 0),
        "aristocrats": len(aristocrats),
        "real_aristocrats": len(real_aristocrats),
        "yield_gt_5pct": len(high_yield),
        "dart_dps_covered": dart_covered,
    }
    rows.sort(key=lambda r: r.get("dividend_yield") or 0, reverse=True)
    return {"kpi": kpi, "rows": rows[:50], "aristocrats": aristocrats[:30]}
