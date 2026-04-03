"""Tests for sepa.backtest — portfolio, metrics, and engine basics."""
import math
from sepa.backtest.portfolio import Portfolio
from sepa.backtest.metrics import compute_metrics


class TestPortfolio:
    def test_buy_sell_cycle(self):
        pf = Portfolio(initial_cash=10_000_000, max_positions=5)
        assert pf.buy('A', '20260101', 10000.0, sector='Tech')
        assert 'A' in pf.positions
        assert pf.cash < 10_000_000

        pnl = pf.sell('A', '20260110', 11000.0, reason='signal')
        assert pnl is not None
        assert 'A' not in pf.positions

    def test_max_positions(self):
        pf = Portfolio(initial_cash=100_000_000, max_positions=2)
        assert pf.buy('A', '20260101', 1000.0)
        assert pf.buy('B', '20260101', 1000.0)
        assert not pf.buy('C', '20260101', 1000.0)  # rejected

    def test_stop_loss(self):
        pf = Portfolio(initial_cash=10_000_000, max_positions=5)
        pf.buy('A', '20260101', 10000.0, stop=9250.0)
        stopped = pf.check_stops('20260105', {'A': 9200.0})
        assert 'A' in stopped
        assert 'A' not in pf.positions

    def test_mark_to_market(self):
        pf = Portfolio(initial_cash=10_000_000, max_positions=5)
        pf.buy('A', '20260101', 10000.0)
        equity = pf.mark_to_market('20260101', {'A': 10000.0})
        assert equity > 0
        assert len(pf.equity_curve) == 1

    def test_cost_model(self):
        pf = Portfolio(initial_cash=10_000_000, max_positions=1)
        pf.buy('A', '20260101', 10000.0)
        # Even with same price, selling should result in loss due to costs
        pnl = pf.sell('A', '20260102', 10000.0)
        assert pnl is not None
        assert pnl < 0  # costs eat into it


class TestMetrics:
    def test_basic_metrics(self):
        curve = [
            {'date': f'202601{i:02d}', 'equity': 100_000 * (1 + 0.001 * i)}
            for i in range(1, 253)
        ]
        m = compute_metrics(curve)
        assert m['cagr'] > 0
        assert m['sharpe'] > 0
        assert m['max_drawdown'] <= 0
        assert 0 <= m['win_rate'] <= 1.0

    def test_losing_curve(self):
        curve = [
            {'date': f'202601{i:02d}', 'equity': 100_000 * (1 - 0.001 * i)}
            for i in range(1, 100)
        ]
        m = compute_metrics(curve)
        assert m['total_return'] < 0
        assert m['max_drawdown'] < 0

    def test_empty_curve(self):
        m = compute_metrics([])
        assert m['cagr'] == 0.0

    def test_with_benchmark(self):
        curve = [
            {'date': f'2026{i:04d}', 'equity': 100_000 * (1 + 0.001 * i)}
            for i in range(1, 253)
        ]
        bench_returns = [0.0005] * 252
        m = compute_metrics(curve, benchmark_returns=bench_returns)
        assert 'benchmark' in m
        assert 'alpha' in m['benchmark']
