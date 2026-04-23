"""Simple Fama-French-style factor returns.

Given the daily OHLCV in ky.db + the universe metadata, this computes a
deliberately simple proxy for three academic factors:

- **SIZE (SMB)**   : small minus big — long bottom-quintile by latest close,
  short top-quintile.
- **MOM (UMD)**    : momentum — long top-quintile by trailing 6-month return,
  short bottom-quintile.
- **VAL (HML proxy)** : inverse-price quintile (no book values stored yet) —
  long bottom-close-quintile, short top-close-quintile. Flagged in the result
  meta as *proxy* so callers know this is not rigorous HML.

All values come from :class:`Repository`. Pure-numpy; no pandas/scipy imports.

Output is deliberately small: one timeseries per factor plus summary stats.
Heavy lifting (alpha/beta vs market) is intentionally deferred — see
``docs/20_architecture/LEADER_SCORING_SPEC.md`` for the serious version.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    from ky_core.storage import Repository
    from ky_core.storage.db import get_engine
except Exception:  # pragma: no cover
    Repository = None  # type: ignore
    get_engine = None  # type: ignore


FACTORS = ("SIZE", "MOM", "VAL")


@dataclass
class FactorResult:
    factor: str
    dates: List[str]
    long_returns: List[float]
    short_returns: List[float]
    spread: List[float]
    cumulative: List[float]
    stats: Dict[str, float]
    universe_size: int
    note: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor": self.factor,
            "dates": self.dates,
            "long_returns": [round(x, 6) for x in self.long_returns],
            "short_returns": [round(x, 6) for x in self.short_returns],
            "spread": [round(x, 6) for x in self.spread],
            "cumulative": [round(x, 6) for x in self.cumulative],
            "stats": {k: round(v, 4) for k, v in self.stats.items()},
            "universe_size": self.universe_size,
            "note": self.note,
            "meta": self.meta,
        }


# --------------------------------------------------------------------------- #
# SQL helpers — we bypass the ORM for speed (OHLCV has 10M+ rows).             #
# --------------------------------------------------------------------------- #


def _fetch_closes(start_iso: str, end_iso: str, owner_id: str = "self") -> Dict[str, List[Tuple[str, float]]]:
    """Return ``{symbol: [(date, close), ...]}`` for the given window."""
    if get_engine is None:
        return {}
    eng = get_engine()
    with eng.connect() as conn:
        from sqlalchemy import text
        rows = conn.execute(
            text(
                "SELECT symbol, date, close FROM ohlcv "
                "WHERE owner_id = :owner AND date >= :start AND date <= :end "
                "AND close IS NOT NULL AND close > 0 "
                "ORDER BY symbol, date"
            ),
            {"owner": owner_id, "start": start_iso, "end": end_iso},
        ).all()
    out: Dict[str, List[Tuple[str, float]]] = {}
    for symbol, d, close in rows:
        out.setdefault(symbol, []).append((d, float(close)))
    return out


@lru_cache(maxsize=8)
def _cached_compute(factor: str, lookback_days: int, owner_id: str) -> FactorResult:
    return _compute_impl(factor, lookback_days, owner_id)


def compute_factor_returns(
    factor: str = "MOM",
    lookback_days: int = 252,
    owner_id: str = "self",
    *,
    use_cache: bool = True,
) -> FactorResult:
    """Compute long-short daily returns for one factor over ``lookback_days``."""
    if factor not in FACTORS:
        raise ValueError(f"unknown factor {factor!r}; choose one of {FACTORS}")
    if use_cache:
        return _cached_compute(factor, lookback_days, owner_id)
    return _compute_impl(factor, lookback_days, owner_id)


def _compute_impl(factor: str, lookback_days: int, owner_id: str) -> FactorResult:
    empty = FactorResult(
        factor=factor, dates=[], long_returns=[], short_returns=[],
        spread=[], cumulative=[], stats={},
        universe_size=0, note="storage unavailable",
    )
    if Repository is None or get_engine is None:
        return empty

    end_dt = datetime.utcnow().date()
    # pull a bit extra so we have history for the momentum scoring window
    extra_pad = 180 if factor == "MOM" else 20
    start_dt = end_dt - timedelta(days=lookback_days + extra_pad + 7)

    closes = _fetch_closes(start_dt.isoformat(), end_dt.isoformat(), owner_id=owner_id)
    if not closes:
        return empty.__class__(
            factor=factor, dates=[], long_returns=[], short_returns=[],
            spread=[], cumulative=[], stats={},
            universe_size=0, note="no OHLCV data in window",
        )

    # --- build aligned date axis ---
    all_dates: set[str] = set()
    for series in closes.values():
        for d, _ in series:
            all_dates.add(d)
    dates_sorted = sorted(all_dates)
    # restrict factor return dates to the lookback window proper
    backtest_start_iso = (end_dt - timedelta(days=lookback_days)).isoformat()
    factor_dates = [d for d in dates_sorted if d >= backtest_start_iso]
    if len(factor_dates) < 5:
        return FactorResult(
            factor=factor, dates=[], long_returns=[], short_returns=[],
            spread=[], cumulative=[], stats={},
            universe_size=len(closes),
            note="lookback window too short",
        )

    # For every (symbol) build a dict for O(1) date lookup.
    by_symbol: Dict[str, Dict[str, float]] = {
        sym: dict(pairs) for sym, pairs in closes.items()
    }

    # --- scoring on the day before factor_dates[0] ---
    scoring_anchor = factor_dates[0]
    quintiles_by_day: Dict[str, Tuple[List[str], List[str]]] = {}

    # Rebalance monthly (first date of each month in factor_dates).
    rebalance_dates: List[str] = []
    last_month = ""
    for d in factor_dates:
        mo = d[:7]
        if mo != last_month:
            rebalance_dates.append(d)
            last_month = mo
    # ensure scoring anchor is a rebalance date
    if rebalance_dates[0] != scoring_anchor:
        rebalance_dates.insert(0, scoring_anchor)

    current_long: List[str] = []
    current_short: List[str] = []
    long_rets: List[float] = []
    short_rets: List[float] = []
    dates_kept: List[str] = []

    rebalance_set = set(rebalance_dates)
    prev_date: Optional[str] = None

    for d in factor_dates:
        if d in rebalance_set:
            current_long, current_short = _score_quintiles(
                factor=factor, asof=d, by_symbol=by_symbol, all_dates=dates_sorted,
            )
            quintiles_by_day[d] = (current_long, current_short)
        if prev_date is not None and current_long:
            lr = _basket_return(current_long, prev_date, d, by_symbol)
            sr = _basket_return(current_short, prev_date, d, by_symbol)
            if lr is not None and sr is not None:
                long_rets.append(lr)
                short_rets.append(sr)
                dates_kept.append(d)
        prev_date = d

    spread = [l - s for l, s in zip(long_rets, short_rets)]
    cumulative = []
    cum = 1.0
    for s in spread:
        cum *= 1.0 + s
        cumulative.append(cum - 1.0)

    stats = _basic_stats(spread)

    note = ""
    meta: Dict[str, Any] = {"rebalance": "monthly", "quintile": 20}
    if factor == "VAL":
        note = "proxy — no book/price data yet; uses inverse-close quintile"
        meta["proxy"] = True

    return FactorResult(
        factor=factor,
        dates=dates_kept,
        long_returns=long_rets,
        short_returns=short_rets,
        spread=spread,
        cumulative=cumulative,
        stats=stats,
        universe_size=len(by_symbol),
        note=note,
        meta=meta,
    )


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _score_quintiles(
    *, factor: str, asof: str,
    by_symbol: Dict[str, Dict[str, float]],
    all_dates: Sequence[str],
) -> Tuple[List[str], List[str]]:
    scored: List[Tuple[str, float]] = []
    if factor == "MOM":
        # 6-month (~120 trading day) return
        idx = list(all_dates).index(asof) if asof in all_dates else -1
        if idx < 0:
            return [], []
        j = max(0, idx - 120)
        start_date = all_dates[j]
        for sym, dmap in by_symbol.items():
            if asof in dmap and start_date in dmap:
                try:
                    ret = dmap[asof] / dmap[start_date] - 1.0
                    scored.append((sym, ret))
                except Exception:
                    continue
    elif factor == "SIZE":
        # proxy: use close price as a weak size proxy (lower close ≈ smaller)
        for sym, dmap in by_symbol.items():
            if asof in dmap:
                scored.append((sym, dmap[asof]))
    elif factor == "VAL":
        for sym, dmap in by_symbol.items():
            if asof in dmap:
                # invert price — "cheaper" names get higher score
                p = dmap[asof]
                if p > 0:
                    scored.append((sym, 1.0 / p))
    if len(scored) < 20:
        return [], []
    scored.sort(key=lambda kv: kv[1])
    k = max(1, len(scored) // 5)
    shorts = [s for s, _ in scored[-k:]]          # most expensive / largest
    longs = [s for s, _ in scored[:k]]            # cheapest / smallest
    if factor == "MOM":
        # momentum = long winners, short losers — reverse
        longs, shorts = shorts, longs
    return longs, shorts


def _basket_return(
    syms: Sequence[str], prev: str, curr: str,
    by_symbol: Dict[str, Dict[str, float]],
) -> Optional[float]:
    rets: List[float] = []
    for sym in syms:
        dmap = by_symbol.get(sym, {})
        if prev in dmap and curr in dmap and dmap[prev] > 0:
            rets.append(dmap[curr] / dmap[prev] - 1.0)
    if not rets:
        return None
    return sum(rets) / len(rets)


def _basic_stats(series: Sequence[float]) -> Dict[str, float]:
    if not series:
        return {"mean": 0.0, "std": 0.0, "sharpe": 0.0, "total": 0.0, "n": 0}
    n = len(series)
    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series) / max(1, n - 1)
    std = var ** 0.5
    total = 1.0
    for x in series:
        total *= 1.0 + x
    return {
        "mean": mean * 252,                 # annualised
        "std": std * (252 ** 0.5),
        "sharpe": (mean / std * (252 ** 0.5)) if std > 0 else 0.0,
        "total": total - 1.0,
        "n": n,
    }
