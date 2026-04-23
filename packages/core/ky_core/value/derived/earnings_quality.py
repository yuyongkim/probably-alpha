"""Earnings Quality (Sloan 1996 accruals).

Since CFO is unavailable we use the balance-sheet accrual approximation:

    Accruals_BS = ΔNon-cash current assets − ΔCurrent liabilities
                − depreciation_proxy

With only total_assets / total_liabilities available, we degrade to:

    Accruals_approx = ΔTotal_assets − ΔTotal_liabilities − Net_income

i.e. the residual Δretained-earnings mismatch (a coarse but standard
Sloan proxy when the cash-flow statement is absent). We then scale by
average total assets to make the measure comparable across sizes:

    Sloan ratio = Accruals_approx / ((TA_t + TA_{t−1}) / 2)

Interpretation:

    - Low (negative/tiny) Sloan ratio  → high earnings quality
    - High Sloan ratio                  → income is "paper" (working-cap
                                           expansion), lower quality

We tag the top quartile (worst) and bottom quartile (best).
"""
from __future__ import annotations

import bisect
from typing import Any

from ky_core.storage import Repository

from ._loaders import (
    pit_fy_rows,
    universe_map,
)


def _sloan_ratio(fy: dict[str, Any], prior: dict[str, Any]) -> float | None:
    ta = fy.get("total_assets")
    tl = fy.get("total_liabilities") or 0.0
    ni = fy.get("net_income")
    ta_p = prior.get("total_assets")
    tl_p = prior.get("total_liabilities") or 0.0
    if not ta or not ta_p or ni is None:
        return None
    d_ta = ta - ta_p
    d_tl = tl - tl_p
    accruals = d_ta - d_tl - ni
    avg_ta = (ta + ta_p) / 2
    if avg_ta <= 0:
        return None
    return accruals / avg_ta


def earnings_quality_for(
    symbol: str,
    *,
    repo: Repository | None = None,
) -> dict[str, Any] | None:
    repo = repo or Repository()
    fys = pit_fy_rows(repo).get(symbol)
    if not fys or len(fys) < 2:
        return None
    fy = fys[-1]
    prior = fys[-2]
    sloan = _sloan_ratio(fy, prior)
    if sloan is None:
        return None
    ni = fy.get("net_income")
    ta = fy.get("total_assets") or 0
    meta = universe_map(repo).get(symbol, {})
    return {
        "symbol": symbol,
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "market": meta.get("market"),
        "period_end": fy.get("period_end"),
        "net_income": ni,
        "total_assets": ta,
        "sloan_ratio": sloan,
    }


def earnings_quality_scan(*, repo: Repository | None = None) -> list[dict[str, Any]]:
    repo = repo or Repository()
    fy_map = pit_fy_rows(repo)
    rows: list[dict[str, Any]] = []
    for sym, fys in fy_map.items():
        row = earnings_quality_for(sym, repo=repo)
        if row is not None:
            rows.append(row)
    if not rows:
        return rows
    sorted_vals = sorted(r["sloan_ratio"] for r in rows)
    q1 = sorted_vals[len(sorted_vals) // 4] if sorted_vals else 0
    q3 = sorted_vals[(3 * len(sorted_vals)) // 4] if sorted_vals else 0
    for r in rows:
        sr = r["sloan_ratio"]
        # Rank: lower is better → bottom quartile = "high quality"
        if sr <= q1:
            r["quality_bucket"] = "high"
        elif sr >= q3:
            r["quality_bucket"] = "low"
        else:
            r["quality_bucket"] = "mid"
        # Percentile (lower better)
        idx = bisect.bisect_left(sorted_vals, sr)
        r["sloan_percentile"] = idx / max(len(sorted_vals) - 1, 1)
    rows.sort(key=lambda r: r["sloan_ratio"])
    return rows


def earnings_quality_top(
    *,
    bucket: str = "high",
    n: int = 50,
    repo: Repository | None = None,
) -> list[dict[str, Any]]:
    rows = earnings_quality_scan(repo=repo)
    if bucket == "high":
        rows = [r for r in rows if r["quality_bucket"] == "high"]
    elif bucket == "low":
        rows = [r for r in rows if r["quality_bucket"] == "low"]
        rows.sort(key=lambda r: r["sloan_ratio"], reverse=True)
    return rows[:n]
