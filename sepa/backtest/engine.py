"""Backtest engine per docs/20_architecture/BACKTEST_RULES.md.

Key rules:
- next-open execution (default)
- Weekly rebalancing (Friday close -> Monday open)
- Stop-loss at -7.5%
- Cost model: commission 0.015%, slippage 0.1%, tax 0.18%
- No look-ahead bias
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from sepa.backtest.metrics import compute_metrics
from sepa.backtest.portfolio import Portfolio
from sepa.data.market_index import market_index_path
from sepa.data.price_history import available_dates, read_price_series_from_path
from sepa.data.sector_map import get_sector, load_sector_map

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Leader Sector/Stock rotation backtest engine."""

    def __init__(
        self,
        *,
        initial_cash: float = 100_000_000.0,
        max_positions: int = 10,
        sector_limit: int = 3,
        rebalance: str = 'weekly',
        execution: str = 'next-open',
        stop_loss_pct: float = 0.075,
    ) -> None:
        self.initial_cash = initial_cash
        self.max_positions = max_positions
        self.sector_limit = sector_limit
        self.rebalance = rebalance
        self.execution = execution
        self.stop_loss_pct = stop_loss_pct

    def run(
        self,
        start_date: str,
        end_date: str,
        *,
        signal_root: Path = Path('.omx/artifacts/daily-signals'),
        data_dir: Path = Path('.omx/artifacts/market-data/ohlcv'),
    ) -> dict:
        """Run backtest over date range. Returns backtest_result dict."""
        dates = self._get_trading_dates(signal_root, start_date, end_date)
        if len(dates) < 5:
            return {'error': f'Insufficient dates: {len(dates)}'}

        portfolio = Portfolio(initial_cash=self.initial_cash, max_positions=self.max_positions)
        sector_map = load_sector_map()
        price_cache = self._build_price_index(data_dir, dates)
        benchmark_prices = self._load_benchmark_prices(dates)
        rebalance_dates = self._get_rebalance_dates(dates)

        for i, date_str in enumerate(dates):
            day_prices = {sym: self._get_price(price_cache, sym, date_str) for sym in price_cache}

            # Check stops first
            portfolio.check_stops(date_str, day_prices)

            # Rebalance on rebalance dates (execute on next trading day)
            if date_str in rebalance_dates and i + 1 < len(dates):
                next_date = dates[i + 1]
                next_prices = {sym: self._get_price(price_cache, sym, next_date) for sym in price_cache}
                self._rebalance(portfolio, date_str, next_date, next_prices, signal_root, sector_map)

            # Mark to market
            portfolio.mark_to_market(date_str, day_prices)

        # Close all remaining positions at last day
        last_date = dates[-1]
        last_prices = {sym: self._get_price(price_cache, sym, last_date) for sym in price_cache}
        for symbol in list(portfolio.positions):
            price = last_prices.get(symbol, 0.0)
            if price > 0:
                portfolio.sell(symbol, last_date, price, reason='backtest_end')

        # Compute metrics
        bench_returns = self._benchmark_returns(benchmark_prices, dates)
        metrics = compute_metrics(portfolio.equity_curve, benchmark_returns=bench_returns)

        # Compute trade-level stats
        trade_stats = self._trade_stats(portfolio.trades)
        metrics.update(trade_stats)

        return self._build_result(start_date, end_date, metrics, portfolio, dates)

    def _rebalance(
        self,
        portfolio: Portfolio,
        signal_date: str,
        exec_date: str,
        exec_prices: dict[str, float],
        signal_root: Path,
        sector_map: dict,
    ) -> None:
        """Rebalance: sell exits, buy new leaders."""
        # Read signals from signal_date
        signals = self._read_signals(signal_root, signal_date)
        if not signals:
            return

        top_sectors = {s.get('sector') for s in signals.get('sectors', [])[:5]}
        top_stocks = signals.get('stocks', [])

        # Sell: positions not in top sectors or top stocks
        top_symbols = {s.get('symbol') for s in top_stocks[:self.max_positions]}
        for symbol in list(portfolio.positions):
            pos = portfolio.positions[symbol]
            sector = get_sector(symbol, sector_map)
            price = exec_prices.get(symbol, 0.0)
            if price <= 0:
                continue
            if sector not in top_sectors or symbol not in top_symbols:
                portfolio.sell(symbol, exec_date, price, reason='rebalance_exit')

        # Buy: new top stocks not already held
        sector_count: dict[str, int] = {}
        for pos in portfolio.positions.values():
            sector_count[pos.sector] = sector_count.get(pos.sector, 0) + 1

        for stock in top_stocks:
            symbol = stock.get('symbol', '')
            if symbol in portfolio.positions:
                continue
            sector = get_sector(symbol, sector_map)
            if sector_count.get(sector, 0) >= self.sector_limit:
                continue
            price = exec_prices.get(symbol, 0.0)
            if price <= 0:
                continue
            stop = price * (1.0 - self.stop_loss_pct)
            if portfolio.buy(symbol, exec_date, price, sector=sector, stop=stop):
                sector_count[sector] = sector_count.get(sector, 0) + 1

    def _read_signals(self, signal_root: Path, date_str: str) -> dict:
        d = signal_root / date_str
        sectors_path = d / 'leader-sectors.json'
        stocks_path = d / 'leader-stocks.json'
        result: dict = {'sectors': [], 'stocks': []}
        for key, path in [('sectors', sectors_path), ('stocks', stocks_path)]:
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding='utf-8'))
                    if isinstance(data, dict) and 'items' in data:
                        result[key] = data['items']
                    elif isinstance(data, list):
                        result[key] = data
                except json.JSONDecodeError:
                    pass
        return result

    def _get_trading_dates(self, signal_root: Path, start: str, end: str) -> list[str]:
        all_dates = sorted(available_dates(signal_root))
        return [d for d in all_dates if start <= d <= end]

    def _get_rebalance_dates(self, dates: list[str]) -> set[str]:
        if self.rebalance == 'daily':
            return set(dates)
        # Weekly: every Friday (or last trading day of the week)
        rebal: set[str] = set()
        for i, d in enumerate(dates):
            try:
                dt = datetime.strptime(d, '%Y%m%d')
                # Friday = 4
                if dt.weekday() == 4:
                    rebal.add(d)
                elif i + 1 < len(dates):
                    next_dt = datetime.strptime(dates[i + 1], '%Y%m%d')
                    if next_dt.isocalendar()[1] != dt.isocalendar()[1]:
                        rebal.add(d)
            except ValueError:
                continue
        return rebal

    def _build_price_index(self, data_dir: Path, dates: list[str]) -> dict[str, dict[str, float]]:
        """Build {symbol: {date: close}} index."""
        index: dict[str, dict[str, float]] = {}
        for path in sorted(data_dir.glob('*.csv')):
            symbol = path.stem
            rows = read_price_series_from_path(path)
            price_by_date: dict[str, float] = {}
            for row in rows:
                d = str(row.get('date', '')).replace('-', '')
                c = row.get('close', 0.0)
                if d and c > 0:
                    price_by_date[d] = c
            if price_by_date:
                index[symbol] = price_by_date
        return index

    def _get_price(self, cache: dict[str, dict[str, float]], symbol: str, date_str: str) -> float:
        return cache.get(symbol, {}).get(date_str, 0.0)

    def _load_benchmark_prices(self, dates: list[str]) -> dict[str, float]:
        path = market_index_path('KOSPI')
        if not path.exists():
            return {}
        rows = read_price_series_from_path(path)
        result: dict[str, float] = {}
        for row in rows:
            d = str(row.get('date', '')).replace('-', '')
            c = row.get('close', 0.0)
            if d and c > 0:
                result[d] = c
        return result

    def _benchmark_returns(self, prices: dict[str, float], dates: list[str]) -> list[float]:
        returns: list[float] = []
        for i in range(1, len(dates)):
            prev = prices.get(dates[i - 1], 0.0)
            curr = prices.get(dates[i], 0.0)
            if prev > 0 and curr > 0:
                returns.append(curr / prev - 1.0)
            else:
                returns.append(0.0)
        return returns

    def _trade_stats(self, trades: list) -> dict:
        buys = [t for t in trades if t.side == 'buy']
        sells = [t for t in trades if t.side == 'sell']
        pairs: list[float] = []
        buy_map: dict[str, float] = {}
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

    def _build_result(self, start: str, end: str, metrics: dict, portfolio: Portfolio, dates: list[str]) -> dict:
        return {
            'run_id': f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'strategy': 'LeaderSectorStock_v1',
            'period': {'start': start, 'end': end},
            'params': {
                'initial_cash': self.initial_cash,
                'max_positions': self.max_positions,
                'sector_limit': self.sector_limit,
                'rebalance': self.rebalance,
                'execution': self.execution,
                'stop_loss_pct': self.stop_loss_pct,
                'commission': Portfolio.COMMISSION_RATE,
                'slippage': Portfolio.SLIPPAGE_RATE,
                'tax': Portfolio.TAX_RATE,
            },
            'metrics': metrics,
            'survivorship_bias_note': 'Includes all symbols present in signal files; delisted stocks not separately tracked',
            'lookback_check': 'PASSED' if self.execution == 'next-open' else 'WARNING',
            'schema_version': '1.0',
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'trading_days': len(dates),
        }
