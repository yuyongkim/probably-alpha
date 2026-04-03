"""Pure factor functions for leader scoring.

All functions return normalized values (0~1 unless noted).
Reuses sepa.analysis.indicators for MA calculations.

Spec: docs/20_architecture/LEADER_SCORING_SPEC.md
"""
from __future__ import annotations

from statistics import mean


def _safe_mean(values: list[float], default: float = 0.0) -> float:
    return mean(values) if values else default


def rs_relative(
    closes: list[float],
    bench_closes: list[float],
    window: int,
) -> float:
    """Relative strength vs benchmark over *window* days.

    Returns the excess return (asset return - benchmark return).
    Caller is responsible for converting to percentile across sectors/stocks.
    """
    if len(closes) < window + 1 or len(bench_closes) < window + 1:
        return 0.0
    asset_ret = closes[-1] / closes[-(window + 1)] - 1.0 if closes[-(window + 1)] > 0 else 0.0
    bench_ret = bench_closes[-1] / bench_closes[-(window + 1)] - 1.0 if bench_closes[-(window + 1)] > 0 else 0.0
    return asset_ret - bench_ret


def breadth_above_ma(
    sector_closes_list: list[list[float]],
    window: int = 50,
) -> float:
    """Fraction of stocks in a sector whose close > MA(window). Range: 0~1."""
    if not sector_closes_list:
        return 0.0
    count = 0
    for closes in sector_closes_list:
        if len(closes) < window:
            continue
        ma = _safe_mean(closes[-window:])
        if closes[-1] > ma:
            count += 1
    total = len(sector_closes_list)
    return count / total if total > 0 else 0.0


def near_high_ratio(
    sector_closes_list: list[list[float]],
    threshold: float = 0.80,
    lookback: int = 252,
) -> float:
    """Fraction of stocks near their 52-week high. Range: 0~1."""
    if not sector_closes_list:
        return 0.0
    count = 0
    for closes in sector_closes_list:
        w = closes[-lookback:] if len(closes) >= lookback else closes
        if not w:
            continue
        high52 = max(w)
        if high52 > 0 and closes[-1] >= threshold * high52:
            count += 1
    total = len(sector_closes_list)
    return count / total if total > 0 else 0.0


def turnover_trend(
    turnovers: list[float],
    short: int = 20,
    long: int = 60,
) -> float:
    """Ratio of short-term avg turnover to long-term avg. Range: 0~3 (clipped)."""
    if len(turnovers) < long:
        return 1.0
    short_avg = _safe_mean(turnovers[-short:], default=1.0)
    long_avg = _safe_mean(turnovers[-long:], default=1.0)
    if long_avg <= 0:
        return 1.0
    return min(3.0, max(0.0, short_avg / long_avg))


def trend_template_ratio(checks: dict[str, bool]) -> float:
    """Fraction of TT 8 conditions passed. Range: 0~1."""
    if not checks:
        return 0.0
    return sum(1 for v in checks.values() if v) / len(checks)


def near_52w_high(closes: list[float], lookback: int = 252) -> float:
    """Proximity to 52-week high. Range: 0~1."""
    w = closes[-lookback:] if len(closes) >= lookback else closes
    if not w:
        return 0.0
    high52 = max(w)
    if high52 <= 0:
        return 0.0
    return min(1.0, closes[-1] / high52)


def volume_expansion(
    volumes: list[float],
    short: int = 5,
    long: int = 50,
) -> float:
    """Recent volume expansion ratio, normalized to 0~1. Raw ratio clipped to 0~3, then /3."""
    if len(volumes) < long:
        return 0.5
    short_avg = _safe_mean(volumes[-short:], default=1.0)
    long_avg = _safe_mean(volumes[-long:], default=1.0)
    if long_avg <= 0:
        return 0.5
    raw = min(3.0, max(0.0, short_avg / long_avg))
    return raw / 3.0


def volatility_contraction(
    closes: list[float],
    short: int = 10,
    long: int = 50,
) -> float:
    """Volatility contraction: 1 - (ATR_short / ATR_long). Range: 0~1.

    Higher = more contracted (tighter price action).
    """
    if len(closes) < long + 1:
        return 0.5

    def _atr(series: list[float]) -> float:
        ranges = [abs(series[i] - series[i - 1]) for i in range(1, len(series))]
        return _safe_mean(ranges, default=0.0)

    atr_short = _atr(closes[-short:])
    atr_long = _atr(closes[-long:])
    if atr_long <= 0:
        return 0.5
    return min(1.0, max(0.0, 1.0 - atr_short / atr_long))


def earnings_proxy(
    *,
    eps_yoy: float | None = None,
    roe: float | None = None,
    opm: float | None = None,
    turnover_accel: float | None = None,
) -> float:
    """Earnings quality proxy score. Range: 0~1.

    Uses actual EPS/ROE/OPM when available, falls back to turnover acceleration.
    """
    score = 0.0
    sources = 0

    if eps_yoy is not None:
        score += min(1.0, max(0.0, eps_yoy / 0.50))  # 50% YoY = 1.0
        sources += 1
    if roe is not None:
        score += min(1.0, max(0.0, roe / 25.0))  # ROE 25% = 1.0
        sources += 1
    if opm is not None:
        score += min(1.0, max(0.0, opm / 20.0))  # OPM 20% = 1.0
        sources += 1

    if sources > 0:
        return score / sources

    # Fallback: turnover acceleration as proxy
    if turnover_accel is not None:
        return min(1.0, max(0.0, turnover_accel / 2.0))

    return 0.5  # No data available


def to_percentile(values: dict[str, float]) -> dict[str, float]:
    """Convert a dict of {key: raw_value} to {key: percentile (0~1)}."""
    items = sorted(values.items(), key=lambda x: x[1])
    n = len(items)
    if n <= 1:
        return {k: 1.0 for k, _ in items}
    return {k: i / (n - 1) for i, (k, _) in enumerate(items)}
