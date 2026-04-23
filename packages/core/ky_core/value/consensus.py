"""Analyst consensus aggregator — fed by fnguide snapshots.

Each fnguide snapshot carries: ``investment_opinion``, ``consensus_recomm_score``,
``consensus_per``, ``consensus_eps``, ``target_price`` (desktop comp only), plus
``financials_annual[-1]`` (E flag: consensus for the upcoming FY).

We scan every cached snapshot in one SQL hit, then compute:

    - eps_rev    — (consensus_eps − forward_eps_e) / |forward_eps_e|
                   when both present; otherwise None.
    - tp_upside  — (target_price / last_close − 1) when both present.
    - sentiment  — "positive" / "neutral" / "negative" from opinion token.

This is a universe-wide batch query (not per-symbol loops), so the whole scan
costs one ``SELECT`` + a few thousand JSON parses — sub-second on 4.5k rows.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from sqlalchemy import text

from ky_core.storage import Repository

log = logging.getLogger(__name__)

_CACHE_TTL_SEC = 3600.0
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}

POSITIVE_OPINIONS = ("buy", "strong buy", "매수", "적극매수", "outperform")
NEGATIVE_OPINIONS = ("sell", "reduce", "매도", "underperform", "축소")


def _load_all_snapshots(repo: Repository) -> list[dict[str, Any]]:
    """Bulk read every fnguide snapshot for the current owner.

    Returns a list of dicts: ``{symbol, name, sector, market, payload}``.
    """
    q = text(
        """
        SELECT f.symbol, f.payload, u.name, u.sector, u.market
        FROM fnguide_snapshots f
        LEFT JOIN universe u
               ON u.ticker = f.symbol
              AND u.owner_id = f.owner_id
        WHERE f.owner_id = :oid
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()

    out: list[dict[str, Any]] = []
    for sym, payload_json, name, sector, market in rows:
        if not payload_json:
            continue
        try:
            payload = json.loads(payload_json)
        except Exception:  # noqa: BLE001
            continue
        out.append(
            {
                "symbol": sym,
                "name": name,
                "sector": sector,
                "market": market,
                "payload": payload,
            }
        )
    return out


def _latest_close(repo: Repository, symbols: list[str]) -> dict[str, float]:
    """One SQL pull for the most recent close per symbol."""
    if not symbols:
        return {}
    closes: dict[str, float] = {}
    for chunk_start in range(0, len(symbols), 500):
        chunk = symbols[chunk_start : chunk_start + 500]
        placeholders = ",".join([f":s{i}" for i in range(len(chunk))])
        params: dict[str, Any] = {f"s{i}": s for i, s in enumerate(chunk)}
        params["oid"] = repo.owner_id
        q = text(
            f"""
            SELECT symbol, close
            FROM ohlcv o
            WHERE owner_id = :oid
              AND symbol IN ({placeholders})
              AND date = (
                  SELECT MAX(date) FROM ohlcv
                  WHERE owner_id = :oid AND symbol = o.symbol
              )
            """
        )
        with repo.session() as sess:
            rows = sess.execute(q, params).fetchall()
        for sym, close in rows:
            if close is not None:
                closes[sym] = float(close)
    return closes


def _sentiment_from_opinion(raw: str | None) -> str:
    if not raw:
        return "neutral"
    s = str(raw).strip().lower()
    if any(tok in s for tok in POSITIVE_OPINIONS):
        return "positive"
    if any(tok in s for tok in NEGATIVE_OPINIONS):
        return "negative"
    return "neutral"


def _forward_eps_estimate(payload: dict[str, Any]) -> float | None:
    """Pick the next-year annual EPS estimate row (is_estimate=true)."""
    annual = payload.get("financials_annual") or []
    # Take the latest-period estimate row.
    est_rows = [r for r in annual if r.get("is_estimate") and r.get("eps") is not None]
    if not est_rows:
        return None
    # Sort by period descending and prefer the furthest-out estimate — the one
    # whose ``consensus_eps`` it should converge to.
    est_rows.sort(key=lambda r: str(r.get("period") or ""), reverse=True)
    try:
        return float(est_rows[0]["eps"])
    except Exception:  # noqa: BLE001
        return None


def consensus_scan(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
    min_covers: int = 0,
) -> list[dict[str, Any]]:
    """Compute per-symbol consensus snapshot across the cached universe."""
    cache_key = f"consensus|covers={min_covers}"
    if use_cache:
        hit = _CACHE.get(cache_key)
        if hit and time.time() - hit[0] <= _CACHE_TTL_SEC:
            return hit[1]

    repo = repo or Repository()
    snaps = _load_all_snapshots(repo)
    closes = _latest_close(repo, [r["symbol"] for r in snaps])

    out: list[dict[str, Any]] = []
    for snap in snaps:
        p = snap["payload"]
        close = closes.get(snap["symbol"])
        opinion = p.get("investment_opinion")
        rec_score = p.get("consensus_recomm_score")
        consensus_eps = p.get("consensus_eps")
        consensus_per = p.get("consensus_per")
        target_price = p.get("target_price")

        forward_eps = _forward_eps_estimate(p)

        # EPS revision proxy: consensus vs. latest E row.
        eps_rev = None
        if consensus_eps is not None and forward_eps and abs(forward_eps) > 1e-6:
            eps_rev = (float(consensus_eps) - forward_eps) / abs(forward_eps)

        tp_upside = None
        if target_price is not None and close and close > 0:
            try:
                tp_upside = float(target_price) / close - 1.0
            except Exception:  # noqa: BLE001
                tp_upside = None

        # Skip rows with no signal at all.
        if consensus_eps is None and target_price is None and opinion is None:
            continue

        out.append(
            {
                "symbol": snap["symbol"],
                "name": snap["name"],
                "sector": snap["sector"],
                "market": snap["market"],
                "close": close,
                "opinion": opinion,
                "recomm_score": rec_score,
                "consensus_per": consensus_per,
                "consensus_eps": consensus_eps,
                "forward_eps_estimate": forward_eps,
                "eps_rev": eps_rev,
                "target_price": target_price,
                "tp_upside": tp_upside,
                "sentiment": _sentiment_from_opinion(opinion),
            }
        )

    if use_cache:
        _CACHE[cache_key] = (time.time(), out)
    return out


def consensus_top(
    *,
    mode: str = "eps_rev",
    n: int = 30,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Sort modes:

        - ``eps_rev``   — biggest positive EPS revision first.
        - ``tp_upside`` — biggest target-price upside first.
        - ``recomm``    — best (lowest) recomm score first (1=strong buy).
    """
    rows = consensus_scan(repo=repo, use_cache=use_cache)
    key_map = {
        "eps_rev": ("eps_rev", True),          # desc
        "tp_upside": ("tp_upside", True),       # desc
        "recomm": ("recomm_score", False),      # asc (lower = more bullish)
    }
    key, desc = key_map.get(mode, key_map["eps_rev"])
    filtered = [r for r in rows if r.get(key) is not None]
    filtered.sort(key=lambda r: r[key], reverse=desc)
    return filtered[:n]


def consensus_summary(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    rows = consensus_scan(repo=repo, use_cache=use_cache)
    kpi = {
        "total": len(rows),
        "positive": sum(1 for r in rows if r["sentiment"] == "positive"),
        "neutral": sum(1 for r in rows if r["sentiment"] == "neutral"),
        "negative": sum(1 for r in rows if r["sentiment"] == "negative"),
        "eps_rev_up": sum(1 for r in rows if (r.get("eps_rev") or 0) > 0.01),
        "eps_rev_down": sum(1 for r in rows if (r.get("eps_rev") or 0) < -0.01),
    }
    top = consensus_top(mode="eps_rev", n=30, repo=repo, use_cache=use_cache)
    return {"kpi": kpi, "rows": top}
