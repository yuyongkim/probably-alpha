"""Backtest result reporting.

Saves backtest_result.json per BACKTEST_RULES.md section 6.
"""
from __future__ import annotations

import json
from pathlib import Path


def save_result(result: dict, output_dir: Path = Path('data/backtest')) -> Path:
    """Save backtest result to JSON file. Returns the file path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = result.get('run_id', 'bt_unknown')
    path = output_dir / f'{run_id}.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def print_summary(result: dict) -> None:
    """Print a human-readable summary to stdout."""
    metrics = result.get('metrics', {})
    params = result.get('params', {})
    period = result.get('period', {})
    bench = metrics.get('benchmark', {})

    print(f"\n{'='*60}")
    print(f"  Backtest Result: {result.get('strategy', '?')}")
    print(f"  Period: {period.get('start', '?')} ~ {period.get('end', '?')}")
    print(f"  Execution: {params.get('execution', '?')}")
    print(f"{'='*60}")
    print(f"  CAGR:          {metrics.get('cagr', 0):.1%}")
    print(f"  Total Return:  {metrics.get('total_return', 0):.1%}")
    print(f"  Sharpe:        {metrics.get('sharpe', 0):.2f}")
    print(f"  Sortino:       {metrics.get('sortino', 0):.2f}")
    print(f"  Max Drawdown:  {metrics.get('max_drawdown', 0):.1%}")
    print(f"  MDD Duration:  {metrics.get('mdd_duration_days', 0)} days")
    print(f"  Win Rate:      {metrics.get('win_rate', 0):.1%}")
    print(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    print(f"  Total Trades:  {metrics.get('total_trades', 0)}")
    if bench:
        print(f"  --- Benchmark ---")
        print(f"  Bench CAGR:    {bench.get('cagr', 0):.1%}")
        print(f"  Alpha:         {bench.get('alpha', 0):.1%}")
        print(f"  Beta:          {bench.get('beta', 0):.2f}")
    print(f"{'='*60}\n")
