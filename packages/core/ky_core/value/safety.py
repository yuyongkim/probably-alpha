"""Margin of Safety + Graham Net-Net filters."""
from __future__ import annotations

from typing import Any

from ky_core.quant.factors import cached_fins, scan
from ky_core.quant.pit import latest_price, ttm_fin
from ky_core.storage import Repository
from ky_core.value.dcf import dcf_value


def margin_of_safety(symbol: str, *, as_of: str | None = None, repo: Repository | None = None) -> dict[str, Any] | None:
    repo = repo or Repository()
    dcf = dcf_value(symbol, as_of=as_of, repo=repo)
    if not dcf or not dcf.get("per_share_value"):
        return None
    price = latest_price(repo, symbol, as_of=as_of)
    if not price or not price.get("close"):
        return None
    intrinsic = dcf["per_share_value"]
    close = price["close"]
    mos = (intrinsic - close) / intrinsic if intrinsic > 0 else None
    return {
        "symbol": symbol,
        "as_of": as_of,
        "price": close,
        "intrinsic": intrinsic,
        "margin_of_safety": mos,
    }


def mos_leaderboard(
    *, as_of: str, n: int = 30, repo: Repository | None = None
) -> list[dict[str, Any]]:
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    out: list[dict[str, Any]] = []
    for r in rows[:600]:  # cap DCF work — MoS leaderboard is expensive
        m = margin_of_safety(r["symbol"], as_of=as_of, repo=repo)
        if m and m.get("margin_of_safety") is not None:
            out.append({**r, **m})
    out.sort(key=lambda x: x["margin_of_safety"] or -1.0, reverse=True)
    return out[:n]


def net_net(
    *, as_of: str, n: int = 30, repo: Repository | None = None
) -> list[dict[str, Any]]:
    """Graham net-net: market cap proxy < 2/3 * (current assets − total liabilities)."""
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    fin_map = cached_fins(as_of, repo=repo)
    out: list[dict[str, Any]] = []
    for r in rows:
        fin = fin_map.get(r["symbol"])
        if not fin or not fin.get("total_assets") or not fin.get("total_liabilities"):
            continue
        current_proxy = fin["total_assets"] * 0.5 - fin["total_liabilities"]
        if current_proxy <= 0:
            continue
        mc_proxy = fin["total_equity"] * 1.5 if fin.get("total_equity") else None
        if not mc_proxy:
            continue
        if mc_proxy < current_proxy * (2 / 3):
            out.append(
                {**r, "mc_proxy": mc_proxy, "ncav_proxy": current_proxy}
            )
    out.sort(key=lambda x: x["mc_proxy"])
    return out[:n]


def deep_value_leaderboard(
    *, as_of: str, n: int = 30, repo: Repository | None = None
) -> list[dict[str, Any]]:
    """Deep-value combo: P/B proxy < 1 and PEG proxy < 1."""
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    fin_map = cached_fins(as_of, repo=repo)
    out: list[dict[str, Any]] = []
    for r in rows:
        fin = fin_map.get(r["symbol"])
        if not fin or not fin.get("total_equity") or not r.get("close"):
            continue
        equity = fin["total_equity"]
        ni = fin.get("net_income_ttm")
        close = r["close"]
        if equity <= 0 or close <= 0:
            continue
        pb = close / equity
        peg = None
        mom = r.get("momentum")
        if ni and ni > 0 and close > 0 and mom is not None:
            pe_proxy = close / ni
            peg = pe_proxy / max(mom + 0.01, 0.01)
        if pb < 1 and (peg is None or peg < 1):
            out.append({**r, "pb": pb, "peg": peg})
    out.sort(key=lambda x: x["pb"])
    return out[:n]
