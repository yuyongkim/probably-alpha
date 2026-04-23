"""Piotroski F-Score — all 9 flags computed from ky.db alone.

Because we don't have cash-flow statement rows, CFO and the accrual flag
rely on the Sloan proxy:

    CFO ≈ NI − ΔWC_proxy, where ΔWC_proxy = Δ(total_assets − total_liabilities)
                                 − net_income_this_year + dividends_this_year

This is the standard accounting identity for the retained-earnings delta.
``ΔRE = NI − DPS × shares`` and ``ΔRE ≈ ΔEquity`` (ignoring stock issuance),
so:

    CFO_proxy ≈ NI + depreciation_proxy − ΔWC

We approximate depreciation as 4% of total_assets (Korean industrial
average 2015-2024). It is rough but stable enough for the accrual flag.

The nine flags:

    1. ROA > 0                 (NI / TA)
    2. CFO > 0                 (proxy above)
    3. ΔROA > 0                (YoY)
    4. Accrual: CFO > NI       (proxy)
    5. Δleverage < 0           (TL/TA down YoY)
    6. Δliquidity > 0          (quick_ratio up — from fnguide snapshot)
    7. No new shares           (shares_outstanding not up YoY)
    8. ΔGross margin > 0       (fnguide ``financial_metrics``)
    9. ΔAsset turnover > 0     (revenue / TA up YoY)

Flag 6 and 7 are based on point-in-time fnguide snapshots rather than a
true YoY delta because the snapshot table only carries the latest row.
When we have ≥2 annual entries inside the payload's ``financials_annual``
and ``financial_metrics`` lists we use them (covers 2021-2026). Otherwise
we mark the flag as unavailable.
"""
from __future__ import annotations

from typing import Any

from ky_core.storage import Repository

from ._loaders import (
    fnguide_payloads,
    pit_fy_rows,
    universe_map,
    safe_div,
)

DEPRECIATION_RATE = 0.04


def _bool_int(b: bool | None) -> int | None:
    return None if b is None else (1 if b else 0)


def _cfo_proxy(fy: dict[str, Any], prior: dict[str, Any] | None) -> float | None:
    """CFO proxy = NI + D&A − ΔWC.

    ΔWC ≈ Δ(total_assets − total_liabilities) when there's no separate WC.
    """
    ni = fy.get("net_income")
    ta = fy.get("total_assets")
    tl = fy.get("total_liabilities")
    if ni is None or ta is None:
        return None
    da = ta * DEPRECIATION_RATE
    if prior is None:
        # First year we can only do NI + D&A
        return ni + da
    ta_p = prior.get("total_assets")
    tl_p = prior.get("total_liabilities")
    if ta_p is None or tl_p is None:
        return ni + da
    d_wc = (ta - (tl or 0.0)) - (ta_p - (tl_p or 0.0))
    return ni + da - d_wc


def _gross_margin(payload: dict[str, Any] | None, year: str) -> float | None:
    """Gross margin for ``year`` from fnguide ``financial_metrics``."""
    if not payload:
        return None
    for row in payload.get("financial_metrics") or []:
        if str(row.get("period")) == str(year) and not row.get("is_estimate"):
            gm = row.get("gross_margin")
            try:
                return float(gm) if gm is not None else None
            except (TypeError, ValueError):
                return None
    return None


def _quick_ratio(payload: dict[str, Any] | None, year: str) -> float | None:
    if not payload:
        return None
    for row in payload.get("financials_annual") or []:
        if str(row.get("period")) == str(year) and not row.get("is_estimate"):
            qr = row.get("quick_ratio")
            try:
                return float(qr) if qr is not None else None
            except (TypeError, ValueError):
                return None
    return None


def _shares_outstanding(payload: dict[str, Any] | None) -> float | None:
    """Latest shares outstanding from fnguide snapshot."""
    if not payload:
        return None
    so = payload.get("shares_outstanding")
    try:
        return float(so) if so is not None else None
    except (TypeError, ValueError):
        return None


def _shares_proxy_prior(payload: dict[str, Any] | None, prior_year: str) -> float | None:
    """Implied prior-year shares = NI / EPS (annuals list)."""
    if not payload:
        return None
    for row in payload.get("financials_annual") or []:
        if str(row.get("period")) == str(prior_year) and not row.get("is_estimate"):
            ni = row.get("net_income")
            eps = row.get("eps")
            if ni and eps and eps > 0:
                try:
                    return float(ni) * 1e8 / float(eps)  # annuals in 억 KRW
                except (TypeError, ValueError):
                    return None
    return None


def _year_str(period_end: str | None) -> str | None:
    if not period_end:
        return None
    return period_end[:4]


def piotroski_full_for(
    symbol: str,
    *,
    repo: Repository | None = None,
) -> dict[str, Any] | None:
    repo = repo or Repository()
    fys = pit_fy_rows(repo).get(symbol)
    if not fys or len(fys) < 1:
        return None
    fy = fys[-1]
    prior = fys[-2] if len(fys) >= 2 else None
    payload = fnguide_payloads(repo).get(symbol)

    ta = fy.get("total_assets")
    tl = fy.get("total_liabilities") or 0.0
    ni = fy.get("net_income")
    rev = fy.get("revenue")
    if not ta or ta <= 0 or ni is None:
        return None

    flags: dict[str, int | None] = {}

    # 1. ROA > 0
    roa_now = safe_div(ni, ta)
    flags["f1_roa_positive"] = _bool_int(roa_now is not None and roa_now > 0)

    # 2. CFO > 0
    cfo_now = _cfo_proxy(fy, prior)
    flags["f2_cfo_positive"] = _bool_int(cfo_now is not None and cfo_now > 0)

    # 3. ΔROA > 0
    if prior:
        roa_prev = safe_div(prior.get("net_income"), prior.get("total_assets"))
        d_roa = (roa_now or 0) - (roa_prev or 0) if roa_now is not None and roa_prev is not None else None
        flags["f3_delta_roa"] = _bool_int(d_roa is not None and d_roa > 0)
    else:
        flags["f3_delta_roa"] = None

    # 4. Accrual: CFO > NI
    flags["f4_accrual"] = _bool_int(cfo_now is not None and cfo_now > ni)

    # 5. Δleverage < 0 (TL/TA)
    if prior:
        lev_now = safe_div(tl, ta)
        lev_prev = safe_div(prior.get("total_liabilities") or 0.0, prior.get("total_assets"))
        d_lev = (lev_now or 0) - (lev_prev or 0) if lev_now is not None and lev_prev is not None else None
        flags["f5_delta_leverage"] = _bool_int(d_lev is not None and d_lev < 0)
    else:
        flags["f5_delta_leverage"] = None

    # 6. Δliquidity > 0 (quick_ratio from fnguide annuals)
    pe_now = _year_str(fy.get("period_end"))
    pe_prev = _year_str(prior.get("period_end")) if prior else None
    qr_now = _quick_ratio(payload, pe_now) if pe_now else None
    qr_prev = _quick_ratio(payload, pe_prev) if pe_prev else None
    if qr_now is not None and qr_prev is not None:
        flags["f6_delta_liquidity"] = _bool_int(qr_now > qr_prev)
    else:
        flags["f6_delta_liquidity"] = None

    # 7. No new shares (shares_outstanding ≤ prior proxy)
    so_now = _shares_outstanding(payload)
    so_prev = _shares_proxy_prior(payload, pe_prev) if pe_prev else None
    if so_now is not None and so_prev is not None and so_prev > 0:
        # Tolerate 0.5% creep from RSUs.
        flags["f7_no_new_shares"] = _bool_int(so_now <= so_prev * 1.005)
    else:
        flags["f7_no_new_shares"] = None

    # 8. Δgross margin > 0
    gm_now = _gross_margin(payload, pe_now) if pe_now else None
    gm_prev = _gross_margin(payload, pe_prev) if pe_prev else None
    if gm_now is not None and gm_prev is not None:
        flags["f8_delta_gross_margin"] = _bool_int(gm_now > gm_prev)
    else:
        flags["f8_delta_gross_margin"] = None

    # 9. Δasset turnover > 0
    if prior and rev is not None and prior.get("revenue") is not None and prior.get("total_assets"):
        at_now = safe_div(rev, ta)
        at_prev = safe_div(prior.get("revenue"), prior.get("total_assets"))
        if at_now is not None and at_prev is not None:
            flags["f9_delta_asset_turnover"] = _bool_int(at_now > at_prev)
        else:
            flags["f9_delta_asset_turnover"] = None
    else:
        flags["f9_delta_asset_turnover"] = None

    score = sum(v for v in flags.values() if isinstance(v, int))
    max_possible = sum(1 for v in flags.values() if v is not None)
    meta = universe_map(repo).get(symbol, {})
    return {
        "symbol": symbol,
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "market": meta.get("market"),
        "period_end": fy.get("period_end"),
        "prior_period_end": prior.get("period_end") if prior else None,
        "flags": flags,
        "score": score,
        "max_possible": max_possible,
        "derived": {
            "roa": roa_now,
            "cfo_proxy": cfo_now,
            "gross_margin_now": gm_now,
            "gross_margin_prev": gm_prev,
            "quick_ratio_now": qr_now,
            "quick_ratio_prev": qr_prev,
            "shares_now": so_now,
            "shares_prev_proxy": so_prev,
        },
    }


def piotroski_full_scan(
    *,
    repo: Repository | None = None,
    min_max_possible: int = 6,
) -> list[dict[str, Any]]:
    """Score every symbol. Only returns rows with ≥ ``min_max_possible`` evaluable flags."""
    repo = repo or Repository()
    fy_map = pit_fy_rows(repo)
    out: list[dict[str, Any]] = []
    for sym in fy_map.keys():
        row = piotroski_full_for(sym, repo=repo)
        if row and row["max_possible"] >= min_max_possible:
            out.append(row)
    out.sort(key=lambda r: (r["score"], r["max_possible"]), reverse=True)
    return out
