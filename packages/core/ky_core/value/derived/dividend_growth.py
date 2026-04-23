"""Dividend Growth Rate (5y CAGR) screener.

Built on top of ``dps.py``. Returns the universe sorted by 5-year DPS
CAGR (DART-backed only — the fnguide proxy never has a time series).
Falls back to net-income CAGR from fnguide ``financials_annual`` when
DART DPS is missing, so the screener never goes empty on a sparse
tenant's DB.
"""
from __future__ import annotations

from typing import Any

from ky_core.storage import Repository

from ._loaders import (
    dps_history,
    fnguide_payloads,
    universe_map,
    fnguide_get,
    cagr,
)


def _ni_cagr(payload: dict[str, Any] | None, years: int = 5) -> float | None:
    if not payload:
        return None
    annual = [
        r for r in (payload.get("financials_annual") or [])
        if not r.get("is_estimate") and r.get("net_income") is not None
    ]
    annual.sort(key=lambda r: str(r.get("period") or ""))
    positives = [float(r["net_income"]) for r in annual if r.get("net_income") and float(r["net_income"]) > 0]
    if len(positives) < years + 1:
        return None
    return cagr(positives[-(years + 1)], positives[-1], years)


def dividend_growth_for(
    symbol: str,
    *,
    repo: Repository | None = None,
    years: int = 5,
) -> dict[str, Any] | None:
    repo = repo or Repository()
    hist = dps_history(repo).get(symbol, [])
    # Dedup per year
    per_year: dict[str, float] = {}
    for r in hist:
        pe = r.get("period_end") or ""
        dps = r.get("dps")
        if dps is None:
            continue
        per_year[pe[:4]] = max(per_year.get(pe[:4], 0.0), float(dps))
    payload = fnguide_payloads(repo).get(symbol)
    meta = universe_map(repo).get(symbol, {})
    source = "dart"
    growth = None
    if len(per_year) >= years + 1:
        series = sorted(per_year.items())
        start = series[-(years + 1)][1]
        end = series[-1][1]
        growth = cagr(start, end, years)
    else:
        growth = _ni_cagr(payload, years=years)
        source = "proxy:ni"
    if growth is None:
        return None
    return {
        "symbol": symbol,
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "market": meta.get("market"),
        "dps_cagr_5y": growth,
        "dividend_yield": fnguide_get(payload, "dividend_yield"),
        "years_reported": len(per_year),
        "source": source,
    }


def dividend_growth_scan(
    *,
    repo: Repository | None = None,
    years: int = 5,
    positive_only: bool = True,
) -> list[dict[str, Any]]:
    repo = repo or Repository()
    hist_map = dps_history(repo)
    out: list[dict[str, Any]] = []
    # DART-backed first
    for sym in hist_map.keys():
        row = dividend_growth_for(sym, repo=repo, years=years)
        if row is not None:
            if positive_only and (row["dps_cagr_5y"] or 0) <= 0:
                continue
            out.append(row)
    out.sort(key=lambda r: r["dps_cagr_5y"], reverse=True)
    return out


def dividend_growth_top(*, n: int = 50, repo: Repository | None = None) -> list[dict[str, Any]]:
    return dividend_growth_scan(repo=repo)[:n]
