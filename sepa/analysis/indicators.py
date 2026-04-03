"""Core math utilities and technical indicators."""
from __future__ import annotations

from statistics import mean


def _to_num(x) -> float:
    try:
        return float(str(x).replace(',', ''))
    except Exception:
        return 0.0


def _round_or_none(value: float | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


def _round_series(values: list[float | None], digits: int = 2) -> list[float | None]:
    return [_round_or_none(v, digits=digits) for v in values]


def linear_regression_slope_intercept(values: list[float]) -> tuple[float, float]:
    n = len(values)
    if n < 2:
        return 0.0, values[0] if values else 0.0

    xs = list(range(n))
    x_mean = mean(xs)
    y_mean = mean(values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return 0.0, y_mean
    slope = numerator / denominator
    intercept = y_mean - slope * x_mean
    return slope, intercept


def moving_average(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    for idx in range(len(values)):
        start = idx + 1 - window
        if start < 0:
            out.append(None)
            continue
        out.append(mean(values[start : idx + 1]))
    return out


def moving_average_nullable(values: list[float | None], window: int) -> list[float | None]:
    out: list[float | None] = []
    for idx in range(len(values)):
        start = idx + 1 - window
        if start < 0:
            out.append(None)
            continue
        part = [value for value in values[start : idx + 1] if isinstance(value, (int, float))]
        out.append(mean(part) if len(part) == window else None)
    return out


def ema(values: list[float], window: int) -> list[float]:
    if not values:
        return []
    alpha = 2.0 / (window + 1.0)
    out = [values[0]]
    for value in values[1:]:
        out.append((value * alpha) + (out[-1] * (1.0 - alpha)))
    return out


def macd(values: list[float], fast: int = 20, slow: int = 60, signal_window: int = 9) -> dict:
    if not values:
        return {'fast': fast, 'slow': slow, 'signal_window': signal_window, 'line': [], 'signal': [], 'histogram': []}

    fast_line = ema(values, fast)
    slow_line = ema(values, slow)
    macd_line = [fast_v - slow_v for fast_v, slow_v in zip(fast_line, slow_line)]
    signal_line = ema(macd_line, signal_window)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    return {
        'fast': fast,
        'slow': slow,
        'signal_window': signal_window,
        'line': _round_series([float(v) for v in macd_line], digits=4),
        'signal': _round_series([float(v) for v in signal_line], digits=4),
        'histogram': _round_series([float(v) for v in histogram], digits=4),
    }


def _rebase_base100(values: list[float | None]) -> list[float | None]:
    base = next((float(value) for value in values if isinstance(value, (int, float)) and value > 0), None)
    if not base:
        return [None] * len(values)
    out: list[float | None] = []
    for value in values:
        if isinstance(value, (int, float)) and value > 0:
            out.append((float(value) / base) * 100.0)
        else:
            out.append(None)
    return out
