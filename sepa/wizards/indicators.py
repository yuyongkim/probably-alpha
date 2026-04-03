"""Technical indicators used by Market Wizards strategies.

Supplements sepa.analysis.stock_analysis with indicators not already present:
RSI, ADX/DI, ATR, Bollinger Bands, rate-of-change, NR7, etc.
"""

from __future__ import annotations

import math
from typing import Sequence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require(values: Sequence[float], minimum: int, name: str) -> None:
    if len(values) < minimum:
        raise ValueError(f'{name} requires >= {minimum} bars, got {len(values)}')


# ---------------------------------------------------------------------------
# Simple / Exponential Moving Average
# ---------------------------------------------------------------------------

def sma(values: Sequence[float], window: int) -> list[float]:
    """Simple moving average.  Returns list same length as *values*; leading
    entries where window is insufficient are filled with NaN."""
    out: list[float] = []
    for i in range(len(values)):
        if i < window - 1:
            out.append(float('nan'))
        else:
            out.append(sum(values[i - window + 1: i + 1]) / window)
    return out


def ema(values: Sequence[float], window: int) -> list[float]:
    """Exponential moving average (Wilder-style for RSI, standard for others)."""
    if not values:
        return []
    k = 2.0 / (window + 1)
    out = [float(values[0])]
    for i in range(1, len(values)):
        out.append(out[-1] + k * (values[i] - out[-1]))
    return out


def wilder_smooth(values: Sequence[float], window: int) -> list[float]:
    """Wilder smoothing (used by RSI / ADX).  1/N decay."""
    if not values:
        return []
    out = [float(values[0])]
    for i in range(1, len(values)):
        out.append((out[-1] * (window - 1) + values[i]) / window)
    return out


# ---------------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------------

def rsi(closes: Sequence[float], period: int = 14) -> list[float]:
    """Relative Strength Index (Wilder).  First *period* values are NaN."""
    n = len(closes)
    out: list[float] = [float('nan')] * n
    if n <= period:
        return out

    gains = [0.0] * n
    losses = [0.0] * n
    for i in range(1, n):
        diff = closes[i] - closes[i - 1]
        if diff > 0:
            gains[i] = diff
        else:
            losses[i] = -diff

    avg_gain = sum(gains[1: period + 1]) / period
    avg_loss = sum(losses[1: period + 1]) / period

    if avg_loss == 0:
        out[period] = 100.0
    else:
        out[period] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            out[i] = 100.0
        else:
            out[i] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    return out


# ---------------------------------------------------------------------------
# ATR (Average True Range)
# ---------------------------------------------------------------------------

def true_range(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
) -> list[float]:
    """True Range series. First value is high-low."""
    n = len(closes)
    tr = [highs[0] - lows[0]] if n else []
    for i in range(1, n):
        tr.append(max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        ))
    return tr


def atr(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> list[float]:
    """Average True Range (Wilder smoothing)."""
    tr = true_range(highs, lows, closes)
    if len(tr) < period:
        return [float('nan')] * len(tr)
    out: list[float] = [float('nan')] * (period - 1)
    avg = sum(tr[:period]) / period
    out.append(avg)
    for i in range(period, len(tr)):
        avg = (avg * (period - 1) + tr[i]) / period
        out.append(avg)
    return out


# ---------------------------------------------------------------------------
# ADX / +DI / -DI
# ---------------------------------------------------------------------------

def adx(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 14,
) -> tuple[list[float], list[float], list[float]]:
    """Returns (adx, plus_di, minus_di) — each a list same length as input.
    Leading entries are NaN where insufficient data."""
    n = len(closes)
    nan = float('nan')
    adx_out = [nan] * n
    pdi_out = [nan] * n
    mdi_out = [nan] * n
    if n < period * 2:
        return adx_out, pdi_out, mdi_out

    # Directional movement
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    tr_list = true_range(highs, lows, closes)

    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        if up > down and up > 0:
            plus_dm[i] = up
        if down > up and down > 0:
            minus_dm[i] = down

    # Wilder smooth TR, +DM, -DM
    sm_tr = wilder_smooth(tr_list[1:], period)
    sm_pdm = wilder_smooth(plus_dm[1:], period)
    sm_mdm = wilder_smooth(minus_dm[1:], period)

    dx_vals: list[float] = []
    for i in range(len(sm_tr)):
        idx = i + 1  # offset by 1 because we skipped first bar
        if idx >= n:
            break
        if sm_tr[i] == 0:
            pdi_out[idx] = 0.0
            mdi_out[idx] = 0.0
            dx_vals.append(0.0)
        else:
            pdi = 100.0 * sm_pdm[i] / sm_tr[i]
            mdi = 100.0 * sm_mdm[i] / sm_tr[i]
            pdi_out[idx] = pdi
            mdi_out[idx] = mdi
            s = pdi + mdi
            dx_vals.append(abs(pdi - mdi) / s * 100.0 if s else 0.0)

    # ADX = Wilder smooth of DX
    if len(dx_vals) >= period:
        adx_smooth = wilder_smooth(dx_vals[period - 1:], period)
        start = period  # offset in dx_vals
        for j, val in enumerate(adx_smooth):
            idx = start + j
            if idx < n:
                adx_out[idx] = val

    return adx_out, pdi_out, mdi_out


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------

def bollinger_bands(
    closes: Sequence[float],
    window: int = 20,
    num_std: float = 2.0,
) -> tuple[list[float], list[float], list[float], list[float]]:
    """Returns (upper, middle, lower, bandwidth%).
    bandwidth% = (upper - lower) / middle × 100."""
    n = len(closes)
    nan = float('nan')
    upper = [nan] * n
    middle = [nan] * n
    lower = [nan] * n
    bw = [nan] * n
    for i in range(window - 1, n):
        chunk = closes[i - window + 1: i + 1]
        avg = sum(chunk) / window
        var = sum((x - avg) ** 2 for x in chunk) / window
        std = math.sqrt(var)
        middle[i] = avg
        upper[i] = avg + num_std * std
        lower[i] = avg - num_std * std
        bw[i] = (upper[i] - lower[i]) / avg * 100.0 if avg else 0.0
    return upper, middle, lower, bw


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------

def macd(
    closes: Sequence[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> tuple[list[float], list[float], list[float]]:
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line, signal_period)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, histogram


# ---------------------------------------------------------------------------
# Stochastic Oscillator
# ---------------------------------------------------------------------------

def stochastic(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[list[float], list[float]]:
    """Returns (%K, %D).  %D = SMA of %K."""
    n = len(closes)
    nan = float('nan')
    k_out = [nan] * n
    for i in range(k_period - 1, n):
        h = max(highs[i - k_period + 1: i + 1])
        lo = min(lows[i - k_period + 1: i + 1])
        if h == lo:
            k_out[i] = 50.0
        else:
            k_out[i] = (closes[i] - lo) / (h - lo) * 100.0
    d_out = sma(k_out, d_period)
    return k_out, d_out


# ---------------------------------------------------------------------------
# Rate of Change / Momentum
# ---------------------------------------------------------------------------

def roc(values: Sequence[float], period: int) -> list[float]:
    """Rate of change: (current - N ago) / N ago × 100."""
    out: list[float] = [float('nan')] * len(values)
    for i in range(period, len(values)):
        prev = values[i - period]
        if prev:
            out[i] = (values[i] - prev) / prev * 100.0
    return out


def momentum(values: Sequence[float], period: int) -> list[float]:
    """Price momentum: current - N periods ago."""
    out: list[float] = [float('nan')] * len(values)
    for i in range(period, len(values)):
        out[i] = values[i] - values[i - period]
    return out


# ---------------------------------------------------------------------------
# Rolling Max / Min
# ---------------------------------------------------------------------------

def rolling_max(values: Sequence[float], window: int) -> list[float]:
    out: list[float] = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        out.append(max(values[start: i + 1]))
    return out


def rolling_min(values: Sequence[float], window: int) -> list[float]:
    out: list[float] = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        out.append(min(values[start: i + 1]))
    return out


# ---------------------------------------------------------------------------
# NR7 (Narrowest Range of 7 days)
# ---------------------------------------------------------------------------

def nr7(
    highs: Sequence[float],
    lows: Sequence[float],
) -> list[bool]:
    """True on bars where today's range is narrowest of last 7 bars."""
    n = len(highs)
    out = [False] * n
    for i in range(6, n):
        today_range = highs[i] - lows[i]
        is_narrowest = True
        for j in range(i - 6, i):
            if highs[j] - lows[j] <= today_range:
                is_narrowest = False
                break
        out[i] = is_narrowest
    return out


# ---------------------------------------------------------------------------
# 52-week high / low
# ---------------------------------------------------------------------------

def week52_high(highs: Sequence[float]) -> float:
    """52-week (252 trading days) highest high."""
    window = min(252, len(highs))
    if not window:
        return 0.0
    return max(highs[-window:])


def week52_low(lows: Sequence[float]) -> float:
    """52-week (252 trading days) lowest low."""
    window = min(252, len(lows))
    if not window:
        return 0.0
    return min(lows[-window:])


# ---------------------------------------------------------------------------
# Relative Strength (vs benchmark / percentile)
# ---------------------------------------------------------------------------

def relative_strength_percentile(
    stock_closes: Sequence[float],
    period: int = 120,
) -> float:
    """Simple RS based on N-day return (0-100 percentile placeholder).
    In production, compare against universe; here return raw momentum score."""
    if len(stock_closes) < period + 1:
        return 50.0
    ret = (stock_closes[-1] - stock_closes[-period]) / stock_closes[-period] * 100.0
    # Rough mapping: -30%→0, 0%→50, +60%→100
    score = max(0.0, min(100.0, 50.0 + ret * (50.0 / 60.0)))
    return round(score, 1)


# ---------------------------------------------------------------------------
# Volume helpers
# ---------------------------------------------------------------------------

def volume_ratio(volumes: Sequence[float], period: int = 20) -> float:
    """Current volume / SMA(volume, period)."""
    if len(volumes) < period + 1:
        return 1.0
    avg = sum(volumes[-period - 1:-1]) / period
    return volumes[-1] / avg if avg else 1.0


def volume_dryup(volumes: Sequence[float], recent: int = 5, base: int = 50) -> float:
    """Recent avg volume / base avg volume."""
    if len(volumes) < base:
        return 1.0
    recent_avg = sum(volumes[-recent:]) / recent if recent else 1.0
    base_avg = sum(volumes[-base:]) / base
    return recent_avg / base_avg if base_avg else 1.0


# ---------------------------------------------------------------------------
# Daily range helpers
# ---------------------------------------------------------------------------

def daily_range_pct(high: float, low: float, close: float) -> float:
    """Intraday range as % of close."""
    return (high - low) / close if close else 0.0


def avg_daily_range_pct(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    period: int = 20,
) -> float:
    if len(closes) < period:
        return 0.0
    total = sum(
        (highs[-period + i] - lows[-period + i]) / closes[-period + i]
        for i in range(period)
        if closes[-period + i]
    )
    return total / period
