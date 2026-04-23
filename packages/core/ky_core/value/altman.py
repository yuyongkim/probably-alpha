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

from ky_core.quant.pit import ttm_fin, ttm_fin_bulk
from ky_core.storage import Repository


def _altman_from_fin(
    symbol: str, fin: dict[str, Any] | None, as_of: str | None
) -> dict[str, Any] | None:
    if not fin:
        return None
    assets = fin.get("total_assets")
    liab = fin.get("total_liabilities")
    equity = fin.get("total_equity")
    rev = fin.get("revenue_ttm")
    op = fin.get("operating_income_ttm")
    if not assets or assets <= 0 or not liab or liab <= 0:
        return None
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


def altman_bulk(
    symbols: list[str],
    *,
    as_of: str,
    repo: Repository | None = None,
) -> dict[str, dict[str, Any]]:
    """Score a universe in one pass using bulk PIT reads."""
    repo = repo or Repository()
    fin_map = ttm_fin_bulk(repo, symbols, as_of=as_of)
    out: dict[str, dict[str, Any]] = {}
    for sym in symbols:
        row = _altman_from_fin(sym, fin_map.get(sym), as_of)
        if row:
            out[sym] = row
    return out


def altman_z(
    symbol: str, *, as_of: str | None = None, repo: Repository | None = None
) -> dict[str, Any] | None:
    """Altman Z-Score — prefers the full 5-variable derived calc.

    Delegates to ``ky_core.value.derived.altman_full`` when any of the
    proxy inputs can be upgraded from real data (retained earnings from
    pit annual sum, market cap from fnguide). Falls back to the legacy
    equity-scaling proxy if derived fails (no fnguide snapshot, too few
    FY rows, etc).
    """
    try:
        from ky_core.value.derived.altman_full import altman_full_for
        result = altman_full_for(symbol, repo=repo)
        if result is not None:
            return {
                "symbol": result["symbol"],
                "as_of": as_of,
                "A_wc_assets": result["X1_wc_assets"],
                "B_re_assets": result["X2_re_assets"],
                "C_ebit_assets": result["X3_ebit_assets"],
                "D_mcap_liab": result["X4_mcap_liab"],
                "E_sales_assets": result["X5_sales_assets"],
                "z_score": result["z_score"],
                "zone": result["zone"],
                "proxy": any(result.get("proxy", {}).values()),
                "proxy_detail": result.get("proxy", {}),
                "period_end": result.get("period_end"),
                "source": "derived.altman_full",
            }
    except Exception:  # noqa: BLE001
        pass
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
