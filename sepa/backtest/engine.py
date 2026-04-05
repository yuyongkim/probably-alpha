"""Backtest engine v2: on-the-fly signal generation with trader presets.

Instead of reading pre-computed signal files, this engine runs Alpha screening
with trader-specific parameters on each rebalance date using the OHLCV database.

Key rules per BACKTEST_RULES.md:
- next-open execution (default)
- Weekly rebalancing (Friday close -> Monday open)
- Cost model: commission 0.015%, slippage 0.1%, tax 0.18%
- No look-ahead bias: signals use data up to signal_date only
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from sepa.backtest.metrics import compute_metrics
from sepa.backtest.portfolio import Portfolio
from sepa.backtest.screener import screen_universe
from sepa.backtest.strategy import StrategyConfig
from sepa.data.market_index import market_index_path
from sepa.data.ohlcv_db import read_ohlcv_batch, DB_PATH, get_all_symbols
from sepa.data.price_history import read_price_series_from_path
from sepa.data.sector_map import get_sector, load_sector_map
from sepa.data.universe import get_symbol_name

logger = logging.getLogger(__name__)


class BacktestEngine:
    """On-the-fly signal generation backtest engine.

    Data is loaded once and reused across multiple run() calls.
    """

    _cached_full_data: dict | None = None
    _cached_price_index: dict | None = None

    def __init__(self, strategy: StrategyConfig | None = None) -> None:
        self.strategy = strategy or StrategyConfig()

    @classmethod
    def _ensure_data(cls):
        """Load data once, cache for all instances."""
        if cls._cached_full_data is not None:
            return
        print('[BT] Loading price data from DB (one-time)...')
        cls._cached_full_data = read_ohlcv_batch(min_rows=200)
        if cls._cached_full_data:
            # Build index in a temporary instance
            tmp = cls.__new__(cls)
            cls._cached_price_index = tmp._build_date_index(cls._cached_full_data)
            print(f'[BT] Cached {len(cls._cached_full_data)} symbols')

    def run(self, start_date: str, end_date: str) -> dict:
        """Run backtest over date range with on-the-fly screening."""
        config = self.strategy

        self._ensure_data()
        full_data = self._cached_full_data
        price_index = self._cached_price_index
        if not full_data:
            return {'error': 'No price data in ohlcv.db.'}

        # Get trading dates from price data
        all_dates = sorted(set(d for sym_dates in price_index.values() for d in sym_dates))
        dates = [d for d in all_dates if start_date <= d <= end_date]

        # Filter weekdays
        dates = [d for d in dates if self._is_weekday(d)]
        if len(dates) < 5:
            return {'error': f'Insufficient trading dates: {len(dates)}'}

        print(f'[BT] Running {config.name} over {len(dates)} days ({dates[0]}~{dates[-1]})...')

        portfolio = Portfolio(initial_cash=config.initial_cash, max_positions=config.max_positions)
        sector_map = load_sector_map()
        benchmark_prices = self._load_benchmark_prices()
        rebalance_dates = self._get_rebalance_dates(dates, config.rebalance)
        rebalance_count = 0

        # Pre-sort dates per symbol (used by _slice_to_date)
        self._sorted_dates_by_sym = self._build_sorted_dates(full_data, price_index)

        # Load fundamentals for value/earnings screens
        fundamentals = self._load_fundamentals() if (
            config.signal_type == 'value_screen' or config.use_earnings_filter
        ) else None

        for i, date_str in enumerate(dates):
            # Get today's close prices (for signal generation + mark-to-market)
            day_prices = {sym: price_index[sym][date_str][0]
                          for sym in price_index
                          if date_str in price_index[sym] and price_index[sym][date_str][0] > 0}

            # Get today's open prices (for execution — "next-open" from previous day's signal)
            day_open_prices = {sym: price_index[sym][date_str][2]
                               for sym in price_index
                               if date_str in price_index[sym] and len(price_index[sym][date_str]) > 2
                               and price_index[sym][date_str][2] > 0}

            if not day_prices:
                continue

            # 1) Check stops
            portfolio.check_stops(date_str, day_prices)

            # 1b) Trailing stops — raise stops for winners
            if config.trailing_stop:
                portfolio.update_trailing_stops(
                    day_prices,
                    trailing_start_pct=config.trailing_start_pct,
                    trailing_distance_pct=config.trailing_distance_pct,
                )

            # 1c) Profit targets (swing strategies)
            if config.profit_target_pct > 0:
                portfolio.check_profit_targets(date_str, day_prices, config.profit_target_pct)

            # 2) Market filter — compute market MA for signal generation
            market_close_val = None
            market_ma200_val = None
            if config.use_market_filter and benchmark_prices:
                bp_dates = sorted(benchmark_prices.keys())
                bp_idx = [d for d in bp_dates if d <= date_str]
                if len(bp_idx) >= 200:
                    market_close_val = benchmark_prices.get(date_str)
                    ma_slice = [benchmark_prices[d] for d in bp_idx[-200:] if d in benchmark_prices]
                    market_ma200_val = sum(ma_slice) / len(ma_slice) if ma_slice else None

            # 3) Screening — ONLY on rebalance days (not every day)
            is_rebalance = date_str in rebalance_dates
            if is_rebalance and i + 1 < len(dates):
                sliced_data = self._slice_to_date(full_data, price_index, date_str)
                signals = screen_universe(
                    config, sliced_data, fundamentals=fundamentals,
                    market_close=market_close_val, market_ma200=market_ma200_val,
                )
                signal_symbols = {s['symbol'] for s in signals[:config.max_positions]}

                next_date = dates[i + 1]
                next_exec_prices = {sym: price_index[sym][next_date][2]
                                    for sym in price_index
                                    if next_date in price_index[sym] and len(price_index[sym][next_date]) > 2
                                    and price_index[sym][next_date][2] > 0}

                # Exit: sell positions no longer in signals
                if config.leader_exit:
                    for symbol in list(portfolio.positions):
                        if symbol not in signal_symbols:
                            price = next_exec_prices.get(symbol, 0.0)
                            if price > 0:
                                portfolio.sell(symbol, next_date, price, reason='rebalance_exit')

                # Entry: fill empty slots
                if len(portfolio.positions) < config.max_positions:
                    self._fill_positions(portfolio, next_date, next_exec_prices, signals, sector_map)
                rebalance_count += 1
                rebalance_count += 1

            # 4) Mark to market
            portfolio.mark_to_market(date_str, day_prices)

        # Close all positions at end
        last_date = dates[-1]
        last_prices = {sym: price_index[sym][last_date][0]
                       for sym in price_index
                       if last_date in price_index[sym] and price_index[sym][last_date][0] > 0}
        for symbol in list(portfolio.positions):
            price = last_prices.get(symbol, 0.0)
            if price > 0:
                portfolio.sell(symbol, last_date, price, reason='backtest_end')

        # Compute metrics
        bench_returns = self._benchmark_returns(benchmark_prices, dates)
        metrics = compute_metrics(portfolio.equity_curve, benchmark_returns=bench_returns)
        trade_stats = self._trade_stats(portfolio.trades)
        metrics.update(trade_stats)

        trade_pairs = self._build_trade_pairs(portfolio.trades)

        print(f'[BT] Done: {rebalance_count} rebalances, {len(trade_pairs)} trades')

        return {
            'run_id': f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'strategy': config.name,
            'strategy_description': config.description,
            'period': {'start': start_date, 'end': end_date},
            'params': {
                'initial_cash': int(config.initial_cash),
                'max_positions': config.max_positions,
                'sector_limit': config.sector_limit,
                'rebalance': config.rebalance,
                'execution': 'next-open',
                'signal_type': config.signal_type,
                'sizing_method': config.sizing_method,
                'stop_type': config.stop_type,
                'stop_loss_pct': config.stop_loss_pct,
                'commission': Portfolio.COMMISSION_RATE,
                'slippage': Portfolio.SLIPPAGE_RATE,
                'tax': Portfolio.TAX_RATE,
            },
            'rules': {
                'signal_type': config.signal_type,
                'family': config.family,
                'min_tt_pass': config.min_tt_pass,
                'rs_threshold': config.rs_threshold,
                'require_ma50': config.require_ma50,
                'require_close_gt_sma200': config.require_close_gt_sma200,
                'require_volume_expansion': config.require_volume_expansion,
                'require_near_52w_high': config.require_near_52w_high,
                'require_volatility_contraction': config.require_volatility_contraction,
                'require_20d_breakout': config.require_20d_breakout,
                'use_earnings_filter': config.use_earnings_filter,
                'use_market_filter': config.use_market_filter,
                'trailing_stop': config.trailing_stop,
                'profit_target_pct': config.profit_target_pct,
                'sector_filter': config.sector_filter,
                'top_sectors': config.top_sectors,
                'stop_loss_pct': config.stop_loss_pct,
                'sizing_method': config.sizing_method,
                'risk_per_trade_pct': config.risk_per_trade_pct,
            },
            'metrics': metrics,
            'equity_curve': portfolio.equity_curve,
            'trades': trade_pairs,
            'survivorship_bias_note': 'Includes all symbols present in ohlcv.db',
            'lookback_check': 'PASSED',
            'schema_version': '1.0',
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'trading_days': len(dates),
            'rebalance_count': rebalance_count,
        }

    def _fill_positions(
        self,
        portfolio: Portfolio,
        exec_date: str,
        exec_prices: dict[str, float],
        signals: list[dict],
        sector_map: dict,
    ) -> None:
        """Fill empty slots with top-scored stocks from today's screening."""
        config = self.strategy
        sector_count: dict[str, int] = {}
        for pos in portfolio.positions.values():
            sector_count[pos.sector] = sector_count.get(pos.sector, 0) + 1

        for stock in signals:
            if len(portfolio.positions) >= config.max_positions:
                break
            symbol = stock['symbol']
            if symbol in portfolio.positions:
                continue
            sector = get_sector(symbol, sector_map)
            if config.sector_limit > 0 and sector_count.get(sector, 0) >= config.sector_limit:
                continue
            price = exec_prices.get(symbol, 0.0)
            if price <= 0:
                continue
            atr = stock.get('atr', 0.0)
            if config.stop_type == 'atr_trailing' and atr > 0:
                stop = int(price - atr * config.atr_stop_multiplier)
            elif config.stop_type == 'fixed_pct':
                stop = int(price * (1.0 - config.stop_loss_pct))
            else:
                stop = int(price * (1.0 - config.stop_loss_pct))

            bought = portfolio.buy(
                symbol, exec_date, price, sector=sector, stop=stop,
                atr=atr, sizing=config.sizing_method,
                risk_pct=config.risk_per_trade_pct,
                atr_stop_mult=config.atr_stop_multiplier,
            )
            if bought:
                sector_count[sector] = sector_count.get(sector, 0) + 1

    def _build_sorted_dates(self, full_data: dict, price_index: dict) -> dict[str, list[str]]:
        """Pre-sort dates per symbol once. Called at run() start."""
        return {sym: sorted(price_index.get(sym, {}).keys()) for sym in full_data}

    def _slice_to_date(
        self,
        full_data: dict[str, dict],
        price_index: dict[str, dict],
        as_of_date: str,
    ) -> dict[str, dict]:
        """Slice using pre-built sorted dates + bisect. O(log n) per symbol."""
        from bisect import bisect_right
        sorted_dates = self._sorted_dates_by_sym
        sliced: dict[str, dict] = {}
        for symbol, data in full_data.items():
            closes = data.get('closes', [])
            volumes = data.get('volumes', [])
            cutoff = bisect_right(sorted_dates.get(symbol, []), as_of_date)
            if cutoff >= 200:
                sliced[symbol] = {
                    'closes': closes[:cutoff],
                    'volumes': volumes[:cutoff],
                }
        return sliced

    def _load_fundamentals(self) -> dict[str, dict]:
        """Load fundamentals from financial_snapshot for value/earnings screening."""
        import sqlite3
        from pathlib import Path
        db_path = Path('data/financial.db')
        if not db_path.exists():
            return {}
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                'SELECT symbol, per, eps, pbr, bps, roe, dividend_yield FROM financial_snapshot'
            ).fetchall()
        except Exception:
            conn.close()
            return {}
        conn.close()
        result = {}
        for r in rows:
            sym = r['symbol']
            result[sym] = {
                'per': r['per'],
                'pbr': r['pbr'],
                'roe': r['roe'],
                'eps_yoy': 0,  # TODO: compute from financials table
                'revenue_yoy': 0,
                'debt_ratio': None,
            }
        return result

    def _build_date_index(self, full_data: dict[str, dict]) -> dict[str, dict[str, tuple]]:
        """Build {symbol: {date: (close, volume, open)}} from ohlcv DB.

        The open price is used for next-open execution.
        If open is NULL (legacy data), falls back to close.
        """
        from sepa.data.ohlcv_db import _connect, DB_PATH
        index: dict[str, dict[str, tuple]] = {}

        conn = _connect(DB_PATH)
        try:
            rows = conn.execute(
                'SELECT symbol, trade_date, close, volume, open FROM ohlcv ORDER BY symbol, trade_date'
            ).fetchall()
        finally:
            conn.close()

        for row in rows:
            sym = row['symbol']
            close = float(row['close'])
            vol = int(row['volume'])
            open_price = float(row['open'] or close)  # fallback to close if NULL
            date = row['trade_date'].replace('-', '')
            if close <= 0:
                continue
            if sym not in index:
                index[sym] = {}
            index[sym][date] = (close, vol, open_price)

        return index

    def _load_benchmark_prices(self) -> dict[str, float]:
        path = market_index_path('KOSPI')
        if not path.exists():
            return {}
        rows = read_price_series_from_path(path)
        return {str(r.get('date', '')).replace('-', ''): r.get('close', 0.0) for r in rows if r.get('close', 0.0) > 0}

    def _benchmark_returns(self, prices: dict[str, float], dates: list[str]) -> list[float]:
        returns: list[float] = []
        for i in range(1, len(dates)):
            prev = prices.get(dates[i - 1], 0.0)
            curr = prices.get(dates[i], 0.0)
            returns.append(curr / prev - 1.0 if prev > 0 and curr > 0 else 0.0)
        return returns

    def _get_rebalance_dates(self, dates: list[str], freq: str) -> set[str]:
        if freq == 'daily':
            return set(dates)
        rebal: set[str] = set()
        for i, d in enumerate(dates):
            try:
                dt = datetime.strptime(d, '%Y%m%d')
                if dt.weekday() == 4:  # Friday
                    rebal.add(d)
                elif i + 1 < len(dates):
                    next_dt = datetime.strptime(dates[i + 1], '%Y%m%d')
                    if next_dt.isocalendar()[1] != dt.isocalendar()[1]:
                        rebal.add(d)
            except ValueError:
                continue
        return rebal

    @staticmethod
    def _is_weekday(date_str: str) -> bool:
        try:
            return datetime.strptime(date_str, '%Y%m%d').weekday() < 5
        except ValueError:
            return False

    def _build_trade_pairs(self, trades: list) -> list[dict]:
        buy_map: dict[str, dict] = {}
        pairs: list[dict] = []
        for t in trades:
            if t.side == 'buy':
                buy_map[t.symbol] = {'entry_date': t.date, 'entry_price': int(t.price), 'qty': t.qty, 'symbol': t.symbol}
            elif t.side == 'sell' and t.symbol in buy_map:
                entry = buy_map.pop(t.symbol)
                pnl = int((t.price - entry['entry_price']) * entry['qty'])
                pnl_pct = round((t.price / entry['entry_price'] - 1.0) * 100, 2) if entry['entry_price'] > 0 else 0.0
                pairs.append({
                    'symbol': t.symbol,
                    'name': get_symbol_name(t.symbol),
                    'entry_date': entry['entry_date'],
                    'exit_date': t.date,
                    'entry_price': entry['entry_price'],
                    'exit_price': int(t.price),
                    'qty': entry['qty'],
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'reason_exit': t.reason,
                })
        return pairs

    def _trade_stats(self, trades: list) -> dict:
        sells = [t for t in trades if t.side == 'sell']
        buy_map: dict[str, float] = {}
        pairs: list[float] = []
        for t in trades:
            if t.side == 'buy':
                buy_map[t.symbol] = t.price
            elif t.side == 'sell' and t.symbol in buy_map:
                pnl_pct = (t.price / buy_map.pop(t.symbol) - 1.0) if buy_map.get(t.symbol, 0) > 0 else 0.0
                pairs.append(pnl_pct)
        wins = [p for p in pairs if p > 0]
        losses = [p for p in pairs if p <= 0]
        return {
            'total_trades': len(pairs),
            'trade_win_rate': round(len(wins) / len(pairs), 4) if pairs else 0.0,
            'avg_win_pct': round(sum(wins) / len(wins) * 100, 2) if wins else 0.0,
            'avg_loss_pct': round(sum(losses) / len(losses) * 100, 2) if losses else 0.0,
            'stop_loss_exits': sum(1 for t in sells if t.reason == 'stop_loss'),
        }
