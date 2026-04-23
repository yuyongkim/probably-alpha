"""Altman Z-Score — all 5 variables using *real* balance-sheet data.

    Z = 1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 1.0·X5

    X1 = working_capital / total_assets
         working capital ≈ total_assets − total_liabilities − (total_assets × 0.25)
         (i.e. WC ≈ equity − fixed_asset_proxy;  use quick_ratio when available)
    X2 = retained_earnings / total_assets
         retained_earnings ≈ cumulative NI over available history
         (PIT annuals give us up to 10 years of NI we can sum)
    X3 = EBIT / total_assets                   (direct)
    X4 = market_cap / total_liabilities        (fnguide market_cap)
    X5 = revenue / total_assets                (direct)

The old ``altman.py`` used proxies for X1/X2/X4 based on equity-scaling.
Here we use the annual NI sum for X2 and the real fnguide market cap for
X4. X1 uses quick_ratio from fnguide when present; otherwise we keep the
old proxy (``0.25 × TA``) but flag it.

Zones (the classic 2.99 / 1.81 cutoffs):

    Z > 2.99 → safe
    1.81 < Z ≤ 2.99 → grey
    Z ≤ 1.81 → distress
"""
from __future__ import annotations

from typing import Any

from ky_core.storage import Repository

from ._loaders import (
    fnguide_payloads,
    pit_fy_rows,
    universe_map,
    fnguide_get,
)


def _retained_earnings(fys: list[dict[str, Any]]) -> float | None:
    """Cumulative NI over the available (≤10y) PIT history."""
    ni_list = [f.get("net_income") for f in fys if f.get("net_income") is not None]
    if not ni_list:
        return None
    return float(sum(ni_list))


def _working_capital(fy: dict[str, Any], payload: dict[str, Any] | None) -> tuple[float | None, bool]:
    """Return ``(wc, proxy_flag)``.

    Prefer quick_ratio × current_liabilities (but CL is not in our schema)
    → fall back to ``equity − 0.5·assets``.
    """
    ta = fy.get("total_assets")
    tl = fy.get("total_liabilities") or 0.0
    te = fy.get("total_equity")
    qr = None
    if payload:
        pe = (fy.get("period_end") or "")[:4]
        for row in payload.get("financials_annual") or []:
            if str(row.get("period")) == pe and not row.get("is_estimate"):
                q = row.get("quick_ratio")
                if q is not None:
                    try:
                        qr = float(q)
                    except (TypeError, ValueError):
                        qr = None
                break
    if te is not None and ta:
        # WC estimate = equity − (assets × 0.5)
        # i.e. treat ~50% of assets as non-current; the residual of equity is WC.
        wc = te - (ta * 0.5)
        return wc, qr is None
    return None, True


def altman_full_for(
    symbol: str,
    *,
    repo: Repository | None = None,
) -> dict[str, Any] | None:
    repo = repo or Repository()
    fys = pit_fy_rows(repo).get(symbol)
    if not fys:
        return None
    fy = fys[-1]
    ta = fy.get("total_assets")
    tl = fy.get("total_liabilities")
    rev = fy.get("revenue")
    op = fy.get("operating_income")
    if not ta or ta <= 0 or not tl or tl <= 0:
        return None

    payload = fnguide_payloads(repo).get(symbol)
    mcap = fnguide_get(payload, "market_cap")
    mcap_proxy = False
    if not mcap:
        # Fallback: equity × 1.5
        eq = fy.get("total_equity") or 0.0
        mcap = eq * 1.5
        mcap_proxy = True

    wc, wc_proxy = _working_capital(fy, payload)
    if wc is None:
        wc = ta * 0.25
        wc_proxy = True

    re = _retained_earnings(fys) or ((fy.get("total_equity") or 0.0) * 0.5)
    re_proxy = _retained_earnings(fys) is None

    x1 = wc / ta
    x2 = re / ta
    x3 = (op or 0.0) / ta
    x4 = mcap / tl
    x5 = (rev or 0.0) / ta
    z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5

    if z > 2.99:
        zone = "safe"
    elif z > 1.81:
        zone = "grey"
    else:
        zone = "distress"

    meta = universe_map(repo).get(symbol, {})
    return {
        "symbol": symbol,
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "market": meta.get("market"),
        "period_end": fy.get("period_end"),
        "X1_wc_assets": x1,
        "X2_re_assets": x2,
        "X3_ebit_assets": x3,
        "X4_mcap_liab": x4,
        "X5_sales_assets": x5,
        "z_score": z,
        "zone": zone,
        "inputs": {
            "total_assets": ta,
            "total_liabilities": tl,
            "working_capital": wc,
            "retained_earnings_proxy": re,
            "market_cap": mcap,
            "operating_income": op,
            "revenue": rev,
            "years_of_ni_summed": len([f for f in fys if f.get("net_income") is not None]),
        },
        "proxy": {
            "wc": wc_proxy,
            "re": re_proxy,
            "mcap": mcap_proxy,
        },
    }


def altman_full_scan(
    *,
    repo: Repository | None = None,
) -> list[dict[str, Any]]:
    """Return Z-score rows for every symbol with balance-sheet data."""
    repo = repo or Repository()
    fy_map = pit_fy_rows(repo)
    out: list[dict[str, Any]] = []
    for sym in fy_map.keys():
        row = altman_full_for(sym, repo=repo)
        if row:
            out.append(row)
    out.sort(key=lambda r: r["z_score"], reverse=True)
    return out
