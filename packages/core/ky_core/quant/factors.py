"""Factor library — Value / Quality / Momentum / LowVol / Growth.

Design:
- One universe-wide scan per factor; scores are percentile ranks in [0, 1].
- Composite = simple mean of available factor ranks.
- In-memory TTL cache (5 min) keyed by as_of + universe hash so API
  requests don't re-scan on every hit.

All prices come from ``ohlcv`` (20-year history for 4.5k symbols) and all
fundamentals from ``financials_pit``. No external calls.
"""
from __future__ import annotations

import math
import time
from datetime import datetime, timedelta
from typing import Any, Iterable

from sqlalchemy import text

from ky_core.quant.pit import ttm_fin, ttm_fin_bulk
from ky_core.storage import Repository

_CACHE_TTL_SECONDS = 300
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
# Side-cache for the fundamentals map produced during scan(); downstream
# screeners (academic/value) read from here instead of hitting the DB again.
_FIN_CACHE: dict[str, tuple[float, dict[str, dict[str, Any]]]] = {}

_ALLOWED_MARKETS = ("KOSPI", "KOSDAQ", "KONEX")


def _cache_key(as_of: str, markets: tuple[str, ...]) -> str:
    return f"{as_of}|{','.join(markets)}"


def _percentile_rank(values: list[float | None]) -> list[float | None]:
    """Return percentile ranks in [0, 1]; None values stay None."""
    idx = [(i, v) for i, v in enumerate(values) if v is not None and not math.isnan(v)]
    if not idx:
        return [None] * len(values)
    idx.sort(key=lambda t: t[1])
    n = len(idx)
    ranks: list[float | None] = [None] * len(values)
    for rank_pos, (orig_i, _v) in enumerate(idx):
        ranks[orig_i] = rank_pos / max(n - 1, 1)
    return ranks


def _load_universe(repo: Repository, markets: tuple[str, ...]) -> list[dict[str, Any]]:
    q = text(
        """
        SELECT ticker, market, name, sector, industry
        FROM universe
        WHERE owner_id = :oid
          AND market IN :markets
          AND is_etf = 0
        """.replace(":markets", "(" + ",".join([f"'{m}'" for m in markets]) + ")")
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()
    return [
        {"symbol": r[0], "market": r[1], "name": r[2], "sector": r[3], "industry": r[4]}
        for r in rows
    ]


def _load_price_windows(
    repo: Repository, symbols: Iterable[str], as_of: str
) -> dict[str, dict[str, Any]]:
    """For each symbol return {close, close_1m, close_12m, ret_252, vol_252}.

    One SQL query for all symbols in chunks of 500 to stay under SQLite's
    parameter limit.
    """
    start_date = (datetime.fromisoformat(as_of) - timedelta(days=420)).date().isoformat()
    out: dict[str, dict[str, Any]] = {}
    symbols = list(symbols)
    for chunk_start in range(0, len(symbols), 500):
        chunk = symbols[chunk_start : chunk_start + 500]
        placeholders = ",".join([f":s{i}" for i in range(len(chunk))])
        params: dict[str, Any] = {f"s{i}": s for i, s in enumerate(chunk)}
        params["oid"] = repo.owner_id
        params["start"] = start_date
        params["end"] = as_of
        q = text(
            f"""
            SELECT symbol, date, close
            FROM ohlcv
            WHERE owner_id = :oid
              AND symbol IN ({placeholders})
              AND date BETWEEN :start AND :end
            ORDER BY symbol, date ASC
            """
        )
        with repo.session() as sess:
            rows = sess.execute(q, params).fetchall()
        per_sym: dict[str, list[tuple[str, float]]] = {}
        for sym, dt, close in rows:
            per_sym.setdefault(sym, []).append((dt, close))
        for sym, bars in per_sym.items():
            out[sym] = _summarise_bars(bars)
    return out


def _summarise_bars(bars: list[tuple[str, float]]) -> dict[str, Any]:
    if not bars:
        return {"close": None}
    closes = [c for _, c in bars if c is not None and c > 0]
    if len(closes) < 30:
        return {"close": closes[-1] if closes else None}
    close = closes[-1]
    close_1m = closes[-21] if len(closes) >= 21 else None
    close_12m = closes[-252] if len(closes) >= 252 else closes[0]
    ret_12_1 = None
    if close_1m and close_12m and close_12m > 0:
        ret_12_1 = (close_1m / close_12m) - 1.0
    # 252-day daily log-volatility
    log_rets: list[float] = []
    last = None
    for c in closes[-252:]:
        if last is not None and last > 0:
            log_rets.append(math.log(c / last))
        last = c
    if len(log_rets) >= 30:
        mean = sum(log_rets) / len(log_rets)
        var = sum((x - mean) ** 2 for x in log_rets) / max(len(log_rets) - 1, 1)
        vol = math.sqrt(var) * math.sqrt(252)
    else:
        vol = None
    return {
        "close": close,
        "close_1m": close_1m,
        "close_12m": close_12m,
        "ret_12_1m": ret_12_1,
        "vol_252": vol,
    }


def _fundamentals_map(repo: Repository, symbols: list[str], as_of: str) -> dict[str, dict[str, Any]]:
    """One bulk SQL scan instead of per-symbol ``ttm_fin`` calls."""
    return ttm_fin_bulk(repo, symbols, as_of=as_of)


def scan(
    as_of: str,
    markets: tuple[str, ...] = _ALLOWED_MARKETS,
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Compute per-symbol raw factor inputs + percentile ranks.

    Return rows sorted by composite score (desc). Each row:
    ``{symbol, market, name, sector, close, momentum, low_vol, value,
       quality, growth, composite}``.
    """
    key = _cache_key(as_of, markets)
    now = time.time()
    if use_cache and key in _CACHE and now - _CACHE[key][0] < _CACHE_TTL_SECONDS:
        return _CACHE[key][1]
    repo = repo or Repository()
    base = _load_universe(repo, markets)
    symbols = [r["symbol"] for r in base]
    prices = _load_price_windows(repo, symbols, as_of)
    fins = _fundamentals_map(repo, symbols, as_of)
    _FIN_CACHE[key] = (now, fins)
    # Raw values
    rows: list[dict[str, Any]] = []
    for meta in base:
        s = meta["symbol"]
        p = prices.get(s, {})
        f = fins.get(s, {})
        close = p.get("close")
        rev = f.get("revenue_ttm")
        ni = f.get("net_income_ttm")
        equity = f.get("total_equity")
        # Approximate market cap via (price * revenue/ni proxy is unreliable —
        # so we report factor inputs only where data exists.)
        per_proxy = None
        if close and ni and ni > 0:
            # Without shares outstanding, use close / (ni per KRW) normalised per symbol.
            per_proxy = close / ni if ni > 0 else None
        roe = (ni / equity) if ni is not None and equity and equity > 0 else None
        rows.append(
            {
                "symbol": s,
                "market": meta["market"],
                "name": meta["name"],
                "sector": meta["sector"],
                "close": close,
                "_raw_momentum": p.get("ret_12_1m"),
                "_raw_low_vol": (-p["vol_252"]) if p.get("vol_252") else None,
                "_raw_value": (-per_proxy) if per_proxy else None,
                "_raw_quality": roe,
                "_raw_growth": rev,
            }
        )
    # Percentile ranks across each column
    for factor in ("momentum", "low_vol", "value", "quality", "growth"):
        ranks = _percentile_rank([r[f"_raw_{factor}"] for r in rows])
        for r, rank in zip(rows, ranks):
            r[factor] = rank
    for r in rows:
        present = [r[k] for k in ("momentum", "low_vol", "value", "quality", "growth") if r[k] is not None]
        r["composite"] = sum(present) / len(present) if present else None
        # drop raw fields
        for k in list(r.keys()):
            if k.startswith("_raw_"):
                del r[k]
    rows.sort(key=lambda r: (r["composite"] is None, -(r["composite"] or 0.0)))
    if use_cache:
        _CACHE[key] = (now, rows)
    return rows


def top_by_factor(
    as_of: str,
    factor: str,
    *,
    n: int = 50,
    markets: tuple[str, ...] = _ALLOWED_MARKETS,
    repo: Repository | None = None,
) -> list[dict[str, Any]]:
    rows = scan(as_of, markets, repo=repo)
    filt = [r for r in rows if r.get(factor) is not None]
    filt.sort(key=lambda r: r[factor], reverse=True)
    return filt[:n]


def clear_cache() -> None:
    _CACHE.clear()
    _FIN_CACHE.clear()


def cached_fins(
    as_of: str,
    markets: tuple[str, ...] = _ALLOWED_MARKETS,
    *,
    repo: Repository | None = None,
) -> dict[str, dict[str, Any]]:
    """Return the fundamentals map produced by the most recent scan().

    If the cache entry is missing or stale we trigger a scan to populate it.
    Downstream screeners (academic.py, value/*.py) use this to avoid the
    N+1 ``ttm_fin`` calls that previously dominated their latency.
    """
    key = _cache_key(as_of, markets)
    now = time.time()
    hit = _FIN_CACHE.get(key)
    if hit and now - hit[0] < _CACHE_TTL_SECONDS:
        return hit[1]
    # warm the cache via scan()
    scan(as_of, markets, repo=repo)
    hit = _FIN_CACHE.get(key)
    return hit[1] if hit else {}
