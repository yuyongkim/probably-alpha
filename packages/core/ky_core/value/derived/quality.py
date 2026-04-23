"""Composite Quality Score.

Blends five signals into a 0-100 percentile rank:

    - ROIC (10y mean)                — +weighted
    - Gross-margin mean              — +weighted (fnguide)
    - FCF yield                      — +weighted
    - Debt ratio (TL/TA)             — −weighted (lower is better)
    - ROIC stability (std dev)       — −weighted (lower is better)

Each raw value is rank-normalised across the universe to [0,1], then
weighted-averaged with

    w = [ROIC: 0.30, GM: 0.20, FCF: 0.25, Debt: 0.15, Stability: 0.10]

and scaled to 0-100. Returns NaN-free numbers so the UI can sort.
"""
from __future__ import annotations

from typing import Any

from ky_core.storage import Repository

from ._loaders import (
    pit_fy_rows,
    universe_map,
    fnguide_payloads,
)
from .moat_v2 import _gross_margin_series, _period_roic, _period_op_margin
from .fcf_yield import fcf_yield_for

WEIGHTS = {
    "roic": 0.30,
    "gm": 0.20,
    "fcf": 0.25,
    "debt": 0.15,   # lower is better
    "stab": 0.10,   # lower is better
}


def _mean_std(series: list[float]) -> tuple[float, float]:
    if not series:
        return 0.0, 0.0
    n = len(series)
    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series) / max(n - 1, 1)
    return mean, var ** 0.5


def _percentile_rank(values: list[float | None]) -> list[float | None]:
    """Fractional rank in [0,1]; None stays None. Ties share the average rank."""
    present = [(i, v) for i, v in enumerate(values) if v is not None]
    if not present:
        return [None] * len(values)
    present.sort(key=lambda x: x[1])
    n = len(present)
    ranks: list[float | None] = [None] * len(values)
    for pos, (idx, _v) in enumerate(present):
        ranks[idx] = pos / max(n - 1, 1)
    return ranks


def _raw_row(
    symbol: str,
    fys: list[dict[str, Any]],
    payload: dict[str, Any] | None,
    repo: Repository,
) -> dict[str, Any] | None:
    if not fys:
        return None
    recent = fys[-10:]
    roic_series = [x for x in (_period_roic(r) for r in recent) if x is not None]
    if not roic_series:
        return None
    roic_mean, roic_std = _mean_std(roic_series)
    gm_series = _gross_margin_series(payload)
    gm_mean = sum(gm_series) / len(gm_series) if gm_series else None
    latest = fys[-1]
    ta = latest.get("total_assets") or 0
    tl = latest.get("total_liabilities") or 0
    debt_ratio = tl / ta if ta > 0 else None
    fcf = fcf_yield_for(symbol, repo=repo)
    fcf_yield_v = fcf["fcf_yield"] if fcf else None
    meta = universe_map(repo).get(symbol, {})
    return {
        "symbol": symbol,
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "market": meta.get("market"),
        "roic_10y_mean": roic_mean,
        "roic_10y_std": roic_std,
        "gross_margin_mean": gm_mean,
        "debt_ratio": debt_ratio,
        "fcf_yield": fcf_yield_v,
    }


def quality_scan(*, repo: Repository | None = None) -> list[dict[str, Any]]:
    repo = repo or Repository()
    fy_map = pit_fy_rows(repo)
    payloads = fnguide_payloads(repo)
    rows: list[dict[str, Any]] = []
    for sym, fys in fy_map.items():
        row = _raw_row(sym, fys, payloads.get(sym), repo)
        if row is not None:
            rows.append(row)
    # Percentile ranks (negated for "lower is better")
    roic_r = _percentile_rank([r["roic_10y_mean"] for r in rows])
    gm_r = _percentile_rank([r["gross_margin_mean"] for r in rows])
    fcf_r = _percentile_rank([r["fcf_yield"] for r in rows])
    debt_r = _percentile_rank([(-r["debt_ratio"]) if r["debt_ratio"] is not None else None for r in rows])
    stab_r = _percentile_rank([(-r["roic_10y_std"]) if r["roic_10y_std"] is not None else None for r in rows])

    for i, r in enumerate(rows):
        components = {
            "roic": roic_r[i],
            "gm": gm_r[i],
            "fcf": fcf_r[i],
            "debt": debt_r[i],
            "stab": stab_r[i],
        }
        weighted: list[tuple[float, float]] = []  # (weight, normalised value)
        for k, v in components.items():
            if v is None:
                continue
            weighted.append((WEIGHTS[k], v))
        if not weighted:
            r["quality_score"] = None
            r["components"] = components
            continue
        total_w = sum(w for w, _ in weighted)
        score = sum(w * v for w, v in weighted) / total_w
        r["quality_score"] = round(score * 100, 2)
        r["components"] = {k: (round(v * 100, 2) if v is not None else None) for k, v in components.items()}

    rows.sort(key=lambda r: (r["quality_score"] is None, -(r["quality_score"] or 0)))
    return rows


def quality_top(*, n: int = 50, repo: Repository | None = None) -> list[dict[str, Any]]:
    return [r for r in quality_scan(repo=repo) if r.get("quality_score") is not None][:n]
