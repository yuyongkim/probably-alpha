"""Run a backtest against ky.db historical data and save the artefact.

Usage
-----

    python scripts/run_backtest.py --strategy sepa --start 2020-01-01 --end 2026-04-17
    python scripts/run_backtest.py --strategy magic_formula --start 2018-01-01 --end 2026-04-17
    python scripts/run_backtest.py --strategy quality_momentum --start 2018-01-01 --end 2026-04-17
    python scripts/run_backtest.py --strategy value_qmj --start 2018-01-01 --end 2026-04-17

Outputs land in ``~/.ky-platform/data/backtest/run_<id>.json``.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_PKG_CORE = Path(__file__).resolve().parents[1] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

from ky_core.backtest import BacktestConfig, BacktestEngine  # noqa: E402
from ky_core.backtest.strategies import build as build_strategy  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ky-platform real-data backtest runner")
    p.add_argument("--strategy", required=True,
                   choices=["sepa", "magic_formula", "quality_momentum", "value_qmj"])
    p.add_argument("--start", required=True, help="ISO YYYY-MM-DD")
    p.add_argument("--end", required=True, help="ISO YYYY-MM-DD")
    p.add_argument("--initial-cash", type=float, default=100_000_000.0,
                   help="Starting portfolio size in KRW. Default: 100M")
    p.add_argument("--max-positions", type=int, default=10)
    p.add_argument("--stop-loss", type=float, default=0.07,
                   help="Stop-loss fraction below entry. Default: 0.07")
    p.add_argument("--risk-per-trade", type=float, default=0.02,
                   help="Per-trade risk as fraction of equity. Default: 0.02")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    logging.basicConfig(
        format="%(asctime)s %(levelname).1s | %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )
    cfg = BacktestConfig(
        strategy_name=args.strategy,
        start=args.start,
        end=args.end,
        initial_cash=args.initial_cash,
        max_positions=args.max_positions,
        risk_per_trade_pct=args.risk_per_trade,
        stop_loss_pct=args.stop_loss,
    )
    strategy = build_strategy(args.strategy)
    engine = BacktestEngine(cfg)
    run = engine.run(strategy)
    path = engine.save(run)

    m = run.metrics
    print("\n================ BACKTEST SUMMARY =================")
    print(f"Strategy         : {cfg.strategy_name}")
    print(f"Date range       : {cfg.start} → {cfg.end}")
    print(f"Universe         : {run.universe_size:,} symbols")
    print(f"Trading days     : {run.n_trading_days:,}")
    print(f"Trades           : {m.n_trades}")
    print(f"Final equity     : {m.final_equity:,.0f} KRW")
    print(f"Total return     : {m.total_return*100:+.2f}%")
    print(f"CAGR             : {m.cagr*100:+.2f}%")
    print(f"Max Drawdown     : {m.max_drawdown*100:+.2f}%")
    print(f"Sharpe           : {m.sharpe:.2f}")
    print(f"Sortino          : {m.sortino:.2f}")
    print(f"Calmar           : {m.calmar:.2f}")
    print(f"Win rate         : {m.win_rate*100:.1f}%")
    print(f"Profit factor    : {m.profit_factor:.2f}")
    print(f"Avg holding days : {m.avg_holding_days:.1f}")
    print(f"Run artefact     : {path}")
    print("====================================================\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
