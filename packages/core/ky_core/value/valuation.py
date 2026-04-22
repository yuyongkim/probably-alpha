"""EV / EBITDA, ROIC, FCF yield, PER / PBR aggregates."""
from __future__ import annotations

from typing import Any

from ky_core.quant.factors import scan
from ky_core.quant.pit import latest_price, ttm_fin
from ky_core.storage import Repository


def ev_ebitda(symbol: str, *, as_of: str | None = None, repo: Repository | None = None) -> dict[str, Any] | None:
    """EV / EBITDA proxy.

    Since shares outstanding isn't stored, we use equity proxy:
    EV ≈ equity_book * 1.5 + total_liabilities − (cash unavailable → 0)
    EBITDA ≈ operating_income (D&A not split out in our schema).
    """
    repo = repo or Repository()
    fin = ttm_fin(repo, symbol, as_of=as_of)
    if not fin:
        return None
    op = fin.get("operating_income_ttm")
    equity = fin.get("total_equity")
    debt = fin.get("total_liabilities") or 0
    if not op or op <= 0 or not equity or equity <= 0:
        return None
    ev = equity * 1.5 + debt
    ebitda = op  # proxy
    return {
        "symbol": symbol,
        "as_of": as_of,
        "ev": ev,
        "ebitda": ebitda,
        "ev_ebitda": ev / ebitda if ebitda > 0 else None,
    }


def roic(symbol: str, *, as_of: str | None = None, repo: Repository | None = None) -> dict[str, Any] | None:
    repo = repo or Repository()
    fin = ttm_fin(repo, symbol, as_of=as_of)
    if not fin:
        return None
    op = fin.get("operating_income_ttm")
    assets = fin.get("total_assets")
    liab = fin.get("total_liabilities") or 0
    if not op or not assets:
        return None
    invested = assets - liab
    if invested <= 0:
        return None
    return {
        "symbol": symbol,
        "as_of": as_of,
        "roic": op * (1 - 0.22) / invested,
        "invested_capital": invested,
    }


def fcf_yield_leaderboard(
    *, as_of: str, n: int = 30, repo: Repository | None = None
) -> list[dict[str, Any]]:
    """Top N by FCF yield (FCF / EV proxy)."""
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    out: list[dict[str, Any]] = []
    for r in rows:
        ev_row = ev_ebitda(r["symbol"], as_of=as_of, repo=repo)
        if not ev_row or not ev_row["ev"]:
            continue
        fin = ttm_fin(repo, r["symbol"], as_of=as_of)
        if not fin:
            continue
        fcf = (fin.get("operating_income_ttm") or 0) * 0.7
        if fcf <= 0:
            continue
        out.append({**r, "fcf": fcf, "ev": ev_row["ev"], "fcf_yield": fcf / ev_row["ev"]})
    out.sort(key=lambda x: x["fcf_yield"], reverse=True)
    return out[:n]


def roic_leaderboard(
    *, as_of: str, n: int = 30, repo: Repository | None = None
) -> list[dict[str, Any]]:
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    out: list[dict[str, Any]] = []
    for r in rows:
        roi = roic(r["symbol"], as_of=as_of, repo=repo)
        if roi and roi.get("roic"):
            out.append({**r, **roi})
    out.sort(key=lambda x: x["roic"], reverse=True)
    return out[:n]


def evebitda_leaderboard(
    *, as_of: str, n: int = 30, repo: Repository | None = None
) -> list[dict[str, Any]]:
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    out: list[dict[str, Any]] = []
    for r in rows:
        ev_row = ev_ebitda(r["symbol"], as_of=as_of, repo=repo)
        if ev_row and ev_row.get("ev_ebitda"):
            out.append({**r, **ev_row})
    out.sort(key=lambda x: x["ev_ebitda"])
    return out[:n]
