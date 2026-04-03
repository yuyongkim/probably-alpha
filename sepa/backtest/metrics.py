"""Performance metrics for backtest results.

Per docs/20_architecture/BACKTEST_RULES.md section 4.
"""
from __future__ import annotations

import math
from statistics import mean, stdev


def compute_metrics(
    equity_curve: list[dict],
    benchmark_returns: list[float] | None = None,
    risk_free_rate: float = 0.035,
) -> dict:
    """Compute all required performance metrics from an equity curve.

    Parameters
    ----------
    equity_curve : list[dict]
        Each dict has ``date`` and ``equity`` keys.
    benchmark_returns : list[float], optional
        Daily benchmark returns for alpha/beta calculation.
    risk_free_rate : float
        Annual risk-free rate (default 3.5%).
    """
    if len(equity_curve) < 2:
        return _empty_metrics()

    equities = [e['equity'] for e in equity_curve]
    daily_returns = [(equities[i] / equities[i - 1] - 1.0) for i in range(1, len(equities)) if equities[i - 1] > 0]

    if not daily_returns:
        return _empty_metrics()

    trading_days = len(daily_returns)
    years = trading_days / 252.0

    # Total return
    total_return = equities[-1] / equities[0] - 1.0 if equities[0] > 0 else 0.0

    # CAGR
    if years > 0 and equities[0] > 0 and equities[-1] > 0:
        cagr = (equities[-1] / equities[0]) ** (1.0 / years) - 1.0
    else:
        cagr = 0.0

    # Volatility (annualized)
    vol = stdev(daily_returns) * math.sqrt(252) if len(daily_returns) > 1 else 0.0

    # Sharpe
    daily_rf = (1.0 + risk_free_rate) ** (1.0 / 252) - 1.0
    excess = [r - daily_rf for r in daily_returns]
    sharpe = (mean(excess) / stdev(excess) * math.sqrt(252)) if len(excess) > 1 and stdev(excess) > 0 else 0.0

    # Sortino
    downside = [r for r in excess if r < 0]
    downside_dev = (sum(r ** 2 for r in downside) / len(downside)) ** 0.5 if downside else 0.0
    sortino = (mean(excess) / downside_dev * math.sqrt(252)) if downside_dev > 0 else 0.0

    # Max Drawdown
    max_dd, mdd_duration = _max_drawdown(equities)

    # Win rate & profit factor from daily returns
    wins = [r for r in daily_returns if r > 0]
    losses = [r for r in daily_returns if r < 0]
    win_rate = len(wins) / len(daily_returns) if daily_returns else 0.0
    total_gain = sum(wins) if wins else 0.0
    total_loss = abs(sum(losses)) if losses else 0.0
    profit_factor = total_gain / total_loss if total_loss > 0 else float('inf') if total_gain > 0 else 0.0

    # Annual turnover (placeholder)
    annual_turnover = 0.0

    result = {
        'cagr': round(cagr, 4),
        'total_return': round(total_return, 4),
        'sharpe': round(sharpe, 2),
        'sortino': round(sortino, 2),
        'max_drawdown': round(max_dd, 4),
        'mdd_duration_days': mdd_duration,
        'volatility': round(vol, 4),
        'win_rate': round(win_rate, 4),
        'profit_factor': round(min(profit_factor, 99.99), 2),
        'annual_turnover': round(annual_turnover, 2),
        'trading_days': trading_days,
    }

    # Benchmark comparison
    if benchmark_returns and len(benchmark_returns) >= len(daily_returns):
        br = benchmark_returns[:len(daily_returns)]
        bench_total = 1.0
        for r in br:
            bench_total *= (1.0 + r)
        bench_total -= 1.0
        bench_cagr = (1.0 + bench_total) ** (1.0 / years) - 1.0 if years > 0 else 0.0
        alpha_val = cagr - bench_cagr

        # Beta
        if len(br) > 1 and stdev(br) > 0:
            cov = sum((daily_returns[i] - mean(daily_returns)) * (br[i] - mean(br)) for i in range(len(br))) / len(br)
            beta_val = cov / (stdev(br) ** 2)
        else:
            beta_val = 1.0

        # Info ratio
        tracking_errors = [daily_returns[i] - br[i] for i in range(len(br))]
        te = stdev(tracking_errors) * math.sqrt(252) if len(tracking_errors) > 1 else 0.0
        info_ratio = (alpha_val / te) if te > 0 else 0.0

        result['benchmark'] = {
            'cagr': round(bench_cagr, 4),
            'total_return': round(bench_total, 4),
            'alpha': round(alpha_val, 4),
            'beta': round(beta_val, 4),
            'info_ratio': round(info_ratio, 2),
        }

    return result


def _max_drawdown(equities: list[float]) -> tuple[float, int]:
    """Returns (max_drawdown_pct, duration_in_days)."""
    peak = equities[0]
    max_dd = 0.0
    dd_start = 0
    max_duration = 0
    current_duration = 0

    for i, eq in enumerate(equities):
        if eq >= peak:
            peak = eq
            current_duration = 0
        else:
            dd = (peak - eq) / peak if peak > 0 else 0.0
            current_duration += 1
            if dd > abs(max_dd):
                max_dd = -dd
            if current_duration > max_duration:
                max_duration = current_duration

    return max_dd, max_duration


def _empty_metrics() -> dict:
    return {
        'cagr': 0.0, 'total_return': 0.0, 'sharpe': 0.0, 'sortino': 0.0,
        'max_drawdown': 0.0, 'mdd_duration_days': 0, 'volatility': 0.0,
        'win_rate': 0.0, 'profit_factor': 0.0, 'annual_turnover': 0.0,
        'trading_days': 0,
    }
