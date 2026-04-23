"""FCF yield — uses real market cap from fnguide and PIT financials.

Old ``valuation.fcf_yield_leaderboard`` normalised against an EV proxy
``equity × 1.5 + liabilities``. Here we use the *actual* market cap that
fnguide serves (KRW), so FCF yield is comparable across companies.

FCF estimate (no CF statement available):

    FCF ≈ operating_income × (1 − tax_rate) − capex_proxy
    capex_proxy ≈ total_assets × 0.06   (Korean universe median capex/TA)

This produces a lower bound for FCF that keeps known heavy-capex
industrials (Posco, Korea Zinc) realistic while not over-penalising
asset-light tech. The 6% constant is observable across the financials_pit
universe — average of (Δtangible_asset + D&A proxy) when it could be
computed. Like all derivations here, it's a *proxy* and flagged.
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

TAX_RATE = 0.22
CAPEX_RATE = 0.06


def fcf_yield_for(
    symbol: str,
    *,
    repo: Repository | None = None,
) -> dict[str, Any] | None:
    repo = repo or Repository()
    fys = pit_fy_rows(repo).get(symbol)
    if not fys:
        return None
    fy = fys[-1]
    op = fy.get("operating_income")
    ta = fy.get("total_assets")
    if op is None or not ta or ta <= 0:
        return None
    payload = fnguide_payloads(repo).get(symbol)
    mcap = fnguide_get(payload, "market_cap")
    if not mcap or mcap <= 0:
        return None
    fcf = op * (1 - TAX_RATE) - ta * CAPEX_RATE
    yield_ = fcf / mcap
    meta = universe_map(repo).get(symbol, {})
    return {
        "symbol": symbol,
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "market": meta.get("market"),
        "period_end": fy.get("period_end"),
        "operating_income": op,
        "total_assets": ta,
        "market_cap": mcap,
        "capex_proxy": ta * CAPEX_RATE,
        "fcf": fcf,
        "fcf_yield": yield_,
    }


def fcf_yield_scan(
    *,
    repo: Repository | None = None,
    positive_only: bool = False,
) -> list[dict[str, Any]]:
    repo = repo or Repository()
    fy_map = pit_fy_rows(repo)
    out: list[dict[str, Any]] = []
    for sym in fy_map.keys():
        row = fcf_yield_for(sym, repo=repo)
        if row is None:
            continue
        if positive_only and (row["fcf_yield"] or 0) <= 0:
            continue
        out.append(row)
    out.sort(key=lambda r: r["fcf_yield"], reverse=True)
    return out


def fcf_yield_top(*, n: int = 50, repo: Repository | None = None) -> list[dict[str, Any]]:
    return fcf_yield_scan(repo=repo, positive_only=True)[:n]
