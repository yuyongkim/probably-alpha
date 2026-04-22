"""SEPA Trend Template (Mark Minervini, "Trade Like a Stock Market Wizard").

Evaluates 8 classical Trend Template conditions on a single symbol
given its daily OHLCV history up to ``as_of``. Callers typically
operate on the wide :class:`~ky_core.scanning.loader.Panel` so this
module only exposes pure functions on a list of closes + volumes.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date as _date
from typing import Any

from ky_core.scanning.loader import Panel, load_panel


@dataclass(frozen=True)
class TrendTemplate:
    symbol: str
    as_of: str
    close_gt_sma150_sma200: bool   # 1. close > SMA150 and close > SMA200
    sma150_gt_sma200: bool          # 2. SMA150 > SMA200
    sma200_rising_1m: bool          # 3. SMA200 rising (>= 1 month)
    sma50_gt_sma150_gt_sma200: bool # 4. SMA50 > SMA150 > SMA200
    close_gt_sma50: bool            # 5. close > SMA50
    price_gt_52w_low_30pct: bool    # 6. price >= 52w low * 1.30
    price_close_to_52w_high: bool   # 7. price within 25% of 52w high
    rs_rating_ge_70: bool           # 8. RS rating >= 70 (0-100 percentile)
    rs_value: float                 # raw 6m RS value
    close: float
    sma50: float
    sma150: float
    sma200: float
    high52w: float
    low52w: float

    @property
    def passes(self) -> int:
        return count_passes(self)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["passes"] = self.passes
        return d


def count_passes(tt: TrendTemplate) -> int:
    return sum([
        tt.close_gt_sma150_sma200,
        tt.sma150_gt_sma200,
        tt.sma200_rising_1m,
        tt.sma50_gt_sma150_gt_sma200,
        tt.close_gt_sma50,
        tt.price_gt_52w_low_30pct,
        tt.price_close_to_52w_high,
        tt.rs_rating_ge_70,
    ])


def evaluate(
    symbol: str,
    as_of: _date | str | None = None,
    *,
    panel: Panel | None = None,
) -> TrendTemplate | None:
    """Evaluate the 8 TT conditions for ``symbol`` at ``as_of``.

    Returns ``None`` if we don't have enough history (< 200 trading days).
    The RS rating is computed vs the whole panel so pass a shared panel
    when scoring many symbols.
    """
    panel = panel or load_panel(as_of)
    rows = panel.series.get(symbol)
    if not rows or len(rows) < 200:
        return None
    closes = [r["close"] for r in rows]
    highs = [r["high"] or r["close"] for r in rows]
    lows = [r["low"] or r["close"] for r in rows]
    return _eval_from_arrays(symbol, panel.as_of, closes, highs, lows, panel)


def _eval_from_arrays(
    symbol: str,
    as_of: str,
    closes: list[float],
    highs: list[float],
    lows: list[float],
    panel: Panel,
) -> TrendTemplate:
    close = closes[-1]
    sma50 = _sma(closes, 50)
    sma150 = _sma(closes, 150)
    sma200 = _sma(closes, 200)
    sma200_1m_ago = _sma(closes[:-22], 200) if len(closes) >= 222 else sma200

    # 52-week window: last 252 trading days (or what we have)
    window = closes[-252:]
    hi52 = max(highs[-252:]) if highs[-252:] else close
    lo52 = min(lows[-252:]) if lows[-252:] else close

    rs_value = _six_month_rs(closes)
    rs_pct = _rs_percentile(symbol, panel, rs_value)

    return TrendTemplate(
        symbol=symbol,
        as_of=as_of,
        close_gt_sma150_sma200=close > sma150 and close > sma200,
        sma150_gt_sma200=sma150 > sma200,
        sma200_rising_1m=sma200 > sma200_1m_ago,
        sma50_gt_sma150_gt_sma200=sma50 > sma150 > sma200,
        close_gt_sma50=close > sma50,
        price_gt_52w_low_30pct=close >= lo52 * 1.30 if lo52 > 0 else False,
        price_close_to_52w_high=close >= hi52 * 0.75 if hi52 > 0 else False,
        rs_rating_ge_70=rs_pct >= 70.0,
        rs_value=rs_value,
        close=close,
        sma50=sma50,
        sma150=sma150,
        sma200=sma200,
        high52w=hi52,
        low52w=lo52,
    )


# --------------------------------------------------------------------------- #
# Internals                                                                   #
# --------------------------------------------------------------------------- #


def _sma(xs: list[float], n: int) -> float:
    if not xs:
        return 0.0
    window = xs[-n:] if len(xs) >= n else xs
    return sum(window) / len(window)


def _six_month_rs(closes: list[float]) -> float:
    """Approximate 6-month price return; proxy for Minervini's 'RS value'."""
    if len(closes) < 126 or closes[-126] <= 0:
        return 0.0
    return closes[-1] / closes[-126] - 1.0


_rs_cache: dict[str, list[tuple[str, float]]] = {}


def _rs_percentile(symbol: str, panel: Panel, value: float) -> float:
    key = panel.as_of
    table = _rs_cache.get(key)
    if table is None:
        table = []
        for sym, rows in panel.series.items():
            if len(rows) < 126:
                continue
            cs = [r["close"] for r in rows]
            if cs[-126] <= 0:
                continue
            table.append((sym, cs[-1] / cs[-126] - 1.0))
        table.sort(key=lambda x: x[1])
        _rs_cache[key] = table
    if not table:
        return 0.0
    # binary-ish search by scan (tables are small enough, ~2500 entries)
    below = sum(1 for _, v in table if v <= value)
    return 100.0 * below / len(table)


def clear_rs_cache() -> None:
    _rs_cache.clear()
