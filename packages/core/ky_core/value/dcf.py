"""Simple 2-stage DCF.

- Stage 1: 5 years of ``growth_high`` growth on estimated FCF
- Terminal: Gordon growth at ``growth_term``
- Discount: WACC (or a user-supplied rate)

FCF is estimated from ``operating_income_ttm`` scaled by an assumed
conversion factor (0.7 — roughly maintaining capex + working capital
drag). The consumer can override every assumption.
"""
from __future__ import annotations

from typing import Any

from ky_core.quant.pit import latest_price, ttm_fin
from ky_core.storage import Repository
from ky_core.value.wacc import wacc as calc_wacc


def estimate_fcf(fin: dict[str, Any], conversion: float = 0.7) -> float | None:
    op = fin.get("operating_income_ttm")
    if op is None:
        return None
    return op * conversion


def shares_outstanding_proxy(
    repo: Repository, symbol: str, fin: dict[str, Any], as_of: str | None
) -> float | None:
    """Infer shares outstanding from (ni / price) heuristics.

    Without a first-class shares-outstanding table we approximate from the
    PIT equity + the most-recent close using book value per KRW of close.
    Rough but consistent across the universe.
    """
    equity = fin.get("total_equity")
    if not equity:
        return None
    px = latest_price(repo, symbol, as_of=as_of)
    if not px or not px.get("close"):
        return None
    # Assume price-to-book ≈ 1.5 on average; shares = equity / (close / 1.5)
    close = px["close"]
    return equity * 1.5 / close


def dcf_value(
    symbol: str,
    *,
    as_of: str | None = None,
    growth_high: float = 0.10,
    years_high: int = 5,
    growth_term: float = 0.025,
    wacc_override: float | None = None,
    fcf_override: float | None = None,
    repo: Repository | None = None,
) -> dict[str, Any] | None:
    repo = repo or Repository()
    fin = ttm_fin(repo, symbol, as_of=as_of)
    if not fin:
        return None
    fcf0 = fcf_override if fcf_override is not None else estimate_fcf(fin)
    if fcf0 is None or fcf0 <= 0:
        return {
            "symbol": symbol,
            "as_of": as_of,
            "enterprise_value": None,
            "per_share_value": None,
            "note": "negative or missing FCF",
        }
    if wacc_override is not None:
        wacc_used = wacc_override
        wacc_info = {"wacc": wacc_override, "override": True}
    else:
        w = calc_wacc(symbol, as_of=as_of, repo=repo)
        wacc_used = (w or {}).get("wacc") or 0.09
        wacc_info = w or {"wacc": wacc_used, "override": False}
    if wacc_used <= growth_term:
        wacc_used = growth_term + 0.02  # numerical safety
    # Stage 1
    stage_cf: list[dict[str, Any]] = []
    pv_stage1 = 0.0
    fcf_t = fcf0
    for t in range(1, years_high + 1):
        fcf_t = fcf_t * (1 + growth_high)
        pv = fcf_t / ((1 + wacc_used) ** t)
        pv_stage1 += pv
        stage_cf.append({"year": t, "fcf": fcf_t, "pv": pv})
    # Terminal
    tv = fcf_t * (1 + growth_term) / (wacc_used - growth_term)
    pv_tv = tv / ((1 + wacc_used) ** years_high)
    enterprise = pv_stage1 + pv_tv
    shares = shares_outstanding_proxy(repo, symbol, fin, as_of)
    per_share = enterprise / shares if shares and shares > 0 else None
    return {
        "symbol": symbol,
        "as_of": as_of,
        "assumptions": {
            "growth_high": growth_high,
            "years_high": years_high,
            "growth_term": growth_term,
            "wacc": wacc_used,
        },
        "fcf0": fcf0,
        "stage1": stage_cf,
        "pv_stage1": pv_stage1,
        "terminal_value": tv,
        "pv_terminal": pv_tv,
        "enterprise_value": enterprise,
        "shares_outstanding_proxy": shares,
        "per_share_value": per_share,
        "wacc_breakdown": wacc_info,
    }
