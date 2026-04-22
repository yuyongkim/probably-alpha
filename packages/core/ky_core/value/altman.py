"""Altman Z-Score for public manufacturers.

Z = 1.2·A + 1.4·B + 3.3·C + 0.6·D + 1.0·E where:
  A = working_capital / total_assets   (unavailable → proxy: 0.25 × assets)
  B = retained_earnings / total_assets (proxy: total_equity × 0.5 / assets)
  C = EBIT / total_assets
  D = market_cap / total_liabilities   (market_cap proxied as equity × 1.5)
  E = sales / total_assets

Where proxies are used we flag ``proxy=True`` and the caller can discount.
"""
from __future__ import annotations

from typing import Any

from ky_core.quant.pit import ttm_fin
from ky_core.storage import Repository


def altman_z(
    symbol: str, *, as_of: str | None = None, repo: Repository | None = None
) -> dict[str, Any] | None:
    repo = repo or Repository()
    fin = ttm_fin(repo, symbol, as_of=as_of)
    if not fin:
        return None
    assets = fin.get("total_assets")
    liab = fin.get("total_liabilities")
    equity = fin.get("total_equity")
    rev = fin.get("revenue_ttm")
    op = fin.get("operating_income_ttm")
    if not assets or assets <= 0 or not liab or liab <= 0:
        return None
    # Proxies
    working_capital_proxy = assets * 0.25
    retained_earnings_proxy = (equity or 0) * 0.5
    market_cap_proxy = (equity or 0) * 1.5
    a = working_capital_proxy / assets
    b = retained_earnings_proxy / assets
    c = (op or 0) / assets
    d = market_cap_proxy / liab if liab > 0 else 0
    e = (rev or 0) / assets
    z = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e
    if z > 2.99:
        zone = "safe"
    elif z > 1.81:
        zone = "grey"
    else:
        zone = "distress"
    return {
        "symbol": symbol,
        "as_of": as_of,
        "A_wc_assets": a,
        "B_re_assets": b,
        "C_ebit_assets": c,
        "D_mcap_liab": d,
        "E_sales_assets": e,
        "z_score": z,
        "zone": zone,
        "proxy": True,
    }
