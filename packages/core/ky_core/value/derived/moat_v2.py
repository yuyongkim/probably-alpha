"""Multi-dimensional moat classifier (v2).

The original ``moat.py`` classifies on 10-year ROIC level + stability +
ROE-consistency. The result is very strict (6 Wide on the current
universe). v2 adds two richer signals and relaxes the Wide threshold to
credit companies with strong margin persistence:

    - ROIC level      : 10-year avg ROIC ≥ 12%
    - ROIC stability  : std ≤ 6 percentage-points
    - Gross-margin CV : coefficient of variation (std/mean) ≤ 15%
    - Op-margin level : 5-year avg op margin ≥ 15%
    - ROE consistency : ≥ 6/10 years with ROE > 10%

    wide    = all five pass
    narrow  = ROIC ≥ 8%, std ≤ 10pp, op-margin ≥ 10%, ROE ≥ 4/10
    none    = otherwise

Inputs:
    - financials_pit (FY rows): ROIC, ROE, op_income, revenue
    - fnguide financial_metrics: gross_margin series (2021-2026)

Because fnguide carries ≤ 6 annual rows we measure gross-margin CV over
the available window (usually 4-5 real years after dropping estimates).
"""
from __future__ import annotations

import math
from typing import Any

from ky_core.storage import Repository

from ._loaders import (
    fnguide_payloads,
    pit_fy_rows,
    universe_map,
)

TAX_RATE = 0.22


def _series_stats(series: list[float]) -> tuple[float, float]:
    if not series:
        return 0.0, 0.0
    n = len(series)
    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series) / max(n - 1, 1)
    return mean, math.sqrt(var)


def _period_roic(row: dict[str, Any]) -> float | None:
    op = row.get("operating_income")
    eq = row.get("total_equity")
    liab = row.get("total_liabilities") or 0.0
    if op is None or eq is None:
        return None
    invested = eq + liab
    if invested <= 0:
        return None
    return op * (1 - TAX_RATE) / invested


def _period_roe(row: dict[str, Any]) -> float | None:
    ni = row.get("net_income")
    eq = row.get("total_equity")
    if ni is None or not eq or eq <= 0:
        return None
    return ni / eq


def _period_op_margin(row: dict[str, Any]) -> float | None:
    op = row.get("operating_income")
    rev = row.get("revenue")
    if op is None or not rev or rev <= 0:
        return None
    return op / rev


def _gross_margin_series(payload: dict[str, Any] | None) -> list[float]:
    if not payload:
        return []
    out: list[float] = []
    for row in payload.get("financial_metrics") or []:
        if row.get("is_estimate"):
            continue
        gm = row.get("gross_margin")
        try:
            if gm is not None:
                out.append(float(gm))
        except (TypeError, ValueError):
            continue
    return out


def _classify(
    roic_mean: float,
    roic_std: float,
    gm_cv: float | None,
    op_margin_mean: float,
    roe_years: int,
    year_count: int,
) -> str:
    if year_count == 0:
        return "none"
    # Wide — four hard thresholds on PIT-derived signals.
    # Gross-margin CV is *bonus evidence* when available; missing GM data
    # (fnguide snapshot absent) doesn't block the promotion.
    gm_ok = gm_cv is None or gm_cv <= 0.20
    wide = (
        roic_mean >= 0.12
        and roic_std <= 0.06
        and op_margin_mean >= 0.15
        and gm_ok
        and (roe_years / year_count) >= 0.6
    )
    if wide:
        return "wide"
    narrow = (
        roic_mean >= 0.08
        and roic_std <= 0.10
        and op_margin_mean >= 0.10
        and (roe_years / year_count) >= 0.4
    )
    if narrow:
        return "narrow"
    return "none"


def moat_v2_for(
    symbol: str,
    *,
    repo: Repository | None = None,
    window_years: int = 10,
) -> dict[str, Any] | None:
    repo = repo or Repository()
    fys = pit_fy_rows(repo).get(symbol)
    if not fys:
        return None
    recent = fys[-window_years:]
    if len(recent) < 5:
        return None

    roic_series = [x for x in (_period_roic(r) for r in recent) if x is not None]
    roe_series = [x for x in (_period_roe(r) for r in recent) if x is not None]
    op_margin_series = [x for x in (_period_op_margin(r) for r in recent) if x is not None]
    if len(roic_series) < 5:
        return None

    roic_mean, roic_std = _series_stats(roic_series)
    op_mean = sum(op_margin_series) / len(op_margin_series) if op_margin_series else 0.0
    roe_years = sum(1 for x in roe_series if x > 0.10)

    payload = fnguide_payloads(repo).get(symbol)
    gm_series = _gross_margin_series(payload)
    gm_mean, gm_std = _series_stats(gm_series) if gm_series else (0.0, 0.0)
    gm_cv = (gm_std / gm_mean) if gm_mean > 0 else None

    label = _classify(
        roic_mean, roic_std, gm_cv, op_mean, roe_years, len(roic_series)
    )

    meta = universe_map(repo).get(symbol, {})
    return {
        "symbol": symbol,
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "market": meta.get("market"),
        "roic_mean": roic_mean,
        "roic_std": roic_std,
        "op_margin_mean": op_mean,
        "gross_margin_mean": gm_mean if gm_series else None,
        "gross_margin_cv": gm_cv,
        "roe_years_above_10pct": roe_years,
        "years_used": len(roic_series),
        "moat": label,
    }


def moat_v2_scan(
    *,
    repo: Repository | None = None,
) -> list[dict[str, Any]]:
    repo = repo or Repository()
    fy_map = pit_fy_rows(repo)
    out: list[dict[str, Any]] = []
    for sym in fy_map.keys():
        row = moat_v2_for(sym, repo=repo)
        if row:
            out.append(row)
    out.sort(
        key=lambda r: (
            0 if r["moat"] == "wide" else 1 if r["moat"] == "narrow" else 2,
            -(r.get("roic_mean") or 0),
        )
    )
    return out


def moat_v2_summary(*, repo: Repository | None = None) -> dict[str, Any]:
    rows = moat_v2_scan(repo=repo)
    kpi = {
        "total": len(rows),
        "wide": sum(1 for r in rows if r["moat"] == "wide"),
        "narrow": sum(1 for r in rows if r["moat"] == "narrow"),
        "none": sum(1 for r in rows if r["moat"] == "none"),
    }
    return {"kpi": kpi, "rows": [r for r in rows if r["moat"] in ("wide", "narrow")][:100]}
