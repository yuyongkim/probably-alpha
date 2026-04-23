"""PEG ratio — PER / (EPS growth rate × 100).

We prefer:
    PER from fnguide snapshot (``per`` field).
    EPS growth from fnguide ``financials_annual`` list (5-year CAGR).

Fallback: when the fnguide EPS CAGR is unavailable we derive EPS growth
from ``net_income`` CAGR (pit FY rows) — noisy but sufficient.

Low PEG (< 1.0) is the classic Lynch "cheap growth" flag. We return
rows with PEG > 0 (i.e. positive growth + positive earnings) so
distressed-for-different-reason names don't pollute the leaderboard.
"""
from __future__ import annotations

from typing import Any

from ky_core.storage import Repository

from ._loaders import (
    fnguide_payloads,
    pit_fy_rows,
    universe_map,
    fnguide_get,
    cagr,
)


def _eps_cagr(payload: dict[str, Any] | None, years: int = 5) -> float | None:
    if not payload:
        return None
    annual = [
        r for r in (payload.get("financials_annual") or [])
        if not r.get("is_estimate") and r.get("eps") is not None
    ]
    annual.sort(key=lambda r: str(r.get("period") or ""))
    eps_series = [float(r["eps"]) for r in annual if r.get("eps") and float(r["eps"]) > 0]
    if len(eps_series) < years + 1:
        if len(eps_series) >= 3:
            # Use available window
            years = len(eps_series) - 1
            return cagr(eps_series[0], eps_series[-1], years)
        return None
    return cagr(eps_series[-(years + 1)], eps_series[-1], years)


def _ni_cagr_pit(fys: list[dict[str, Any]], years: int = 5) -> float | None:
    positives = [float(r["net_income"]) for r in fys if r.get("net_income") and float(r["net_income"]) > 0]
    if len(positives) < years + 1:
        if len(positives) >= 3:
            years = len(positives) - 1
            return cagr(positives[0], positives[-1], years)
        return None
    return cagr(positives[-(years + 1)], positives[-1], years)


MAX_PEG_GROWTH = 0.50  # Cap EPS CAGR at 50%/yr: above this is base-recovery noise.


def peg_for(
    symbol: str,
    *,
    repo: Repository | None = None,
    years: int = 5,
) -> dict[str, Any] | None:
    repo = repo or Repository()
    payload = fnguide_payloads(repo).get(symbol)
    per = fnguide_get(payload, "per")
    if per is None or per <= 0:
        return None
    growth = _eps_cagr(payload, years=years)
    source = "eps"
    if growth is None:
        fys = pit_fy_rows(repo).get(symbol)
        if fys:
            growth = _ni_cagr_pit(fys, years=years)
            source = "ni"
    if growth is None or growth <= 0:
        return None
    # Cap to strip out recovery-from-near-zero outliers that wreck sorting.
    growth_capped = min(growth, MAX_PEG_GROWTH)
    peg = per / (growth_capped * 100.0)
    meta = universe_map(repo).get(symbol, {})
    return {
        "symbol": symbol,
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "market": meta.get("market"),
        "per": per,
        "eps_growth_cagr": growth,
        "eps_growth_used": growth_capped,
        "growth_capped": growth > MAX_PEG_GROWTH,
        "peg": peg,
        "source": source,
    }


def peg_scan(
    *,
    repo: Repository | None = None,
    years: int = 5,
) -> list[dict[str, Any]]:
    repo = repo or Repository()
    payloads = fnguide_payloads(repo)
    out: list[dict[str, Any]] = []
    for sym in payloads.keys():
        row = peg_for(sym, repo=repo, years=years)
        if row is not None:
            out.append(row)
    out.sort(key=lambda r: r["peg"])
    return out


def peg_cheap_growth(*, limit: int = 50, repo: Repository | None = None) -> list[dict[str, Any]]:
    """PEG < 1 with positive growth — Lynch's cheap-growth list."""
    rows = peg_scan(repo=repo)
    return [r for r in rows if r["peg"] < 1.0][:limit]
