"""Unit tests for backtest primitives.

We intentionally do NOT hit ky.db here — those are integration-level
checks and belong in a longer-running suite. These tests validate:

    - CostModel is symmetric and arithmetic is correct.
    - Portfolio sizing respects risk + slot caps.
    - Metrics correctly compute CAGR / MDD / Sharpe / win rate.
    - PanelView enforces point-in-time cutoff.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

_PKG_CORE = Path(__file__).resolve().parents[2]
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

from ky_core.backtest.cost import CostModel  # noqa: E402
from ky_core.backtest.engine import PanelView  # noqa: E402
from ky_core.backtest.metrics import compute_metrics  # noqa: E402
from ky_core.backtest.portfolio import Portfolio  # noqa: E402


def test_cost_model_roundtrip():
    c = CostModel()
    # 0.5 * slippage twice + commissions + tax
    drag = c.roundtrip_drag_pct()
    assert abs(drag - (2 * 0.001 + 0.00015 + 0.00015 + 0.0018)) < 1e-9


def test_cost_buy_and_sell_cash():
    c = CostModel()
    # 1M notional buy → 1M * 1.00015 outflow
    assert abs(c.buy_cash(1_000_000) - 1_000_150) < 1e-6
    # 1M notional sell → 1M * (1 - 0.00015 - 0.0018) inflow
    assert abs(c.sell_cash(1_000_000) - (1_000_000 - 150 - 1800)) < 1e-6


def test_portfolio_sizing_respects_risk_budget():
    port = Portfolio.start(
        initial_cash=100_000_000.0,
        max_positions=10,
        risk_per_trade_pct=0.02,   # 2% risk → 2M KRW at 100M equity
        stop_loss_pct=0.07,        # 7% stop
    )
    shares = port.plan_shares(equity=100_000_000.0, entry_price=10_000.0)
    # risk-based: 2M / (10k * 0.07) = 2857 shares
    # slot cap:   (100M / 10) / 10k = 1000 shares   ← binding
    assert shares == 1000


def test_portfolio_sizing_respects_slot_cap():
    port = Portfolio.start(initial_cash=500_000.0, max_positions=10)
    shares = port.plan_shares(equity=500_000.0, entry_price=1000.0)
    # slot cap = (500k / 10) / 1000 = 50  (binding, tighter than risk-based 142)
    assert shares == 50


def test_portfolio_sizing_tiny_cash_binds():
    port = Portfolio.start(initial_cash=10_000.0, max_positions=10)
    # equity still 100k but wallet has only 10k — cash ceiling binds
    shares = port.plan_shares(equity=100_000.0, entry_price=1000.0)
    # 0.97 * 10_000 / 1000 = 9 shares
    assert shares == 9


def test_metrics_on_monotonic_curve():
    equity = [
        {"date": f"2024-01-{d:02d}", "equity": 100_000 * (1.0 + 0.001 * d)}
        for d in range(1, 20)
    ]
    trades = [
        {"pnl": 5000, "pnl_pct": 0.05, "holding_days": 7},
        {"pnl": -2000, "pnl_pct": -0.02, "holding_days": 4},
        {"pnl": 3000, "pnl_pct": 0.03, "holding_days": 10},
    ]
    m = compute_metrics(equity, trades)
    assert m.n_trades == 3
    assert m.win_rate == pytest_approx(2 / 3)
    assert m.final_equity > 100_000
    assert m.total_return > 0
    # monotonic growth → no drawdown
    assert m.max_drawdown == 0.0
    assert m.cagr > 0


def test_panel_view_cutoff():
    series = {
        "A": [
            {"date": "2024-01-01", "close": 100.0, "high": 100.0, "low": 100.0},
            {"date": "2024-01-02", "close": 101.0, "high": 101.0, "low": 101.0},
            {"date": "2024-01-03", "close": 102.0, "high": 102.0, "low": 102.0},
            {"date": "2024-01-04", "close": 103.0, "high": 103.0, "low": 103.0},
        ],
    }
    view = PanelView(_series=series, _universe={}, _cutoff="2024-01-02")
    closes = view.closes_up_to("A")
    assert closes == [100.0, 101.0]     # nothing after cutoff
    recent = view.closes_up_to("A", n=1)
    assert recent == [101.0]
    # available_symbols cares about history length, not universe membership
    assert "A" in view.available_symbols(min_history_days=2)


def pytest_approx(expected: float, rel: float = 1e-6) -> float:
    # tiny shim so we don't require pytest.approx import path
    class _A:
        def __eq__(self, other: object) -> bool:
            if not isinstance(other, (int, float)):
                return NotImplemented
            return abs(other - expected) <= max(abs(expected), 1.0) * rel
        def __repr__(self) -> str:
            return f"approx({expected})"
    return _A()  # type: ignore[return-value]


if __name__ == "__main__":
    # Allow quick smoke `python test_engine_primitives.py`
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"OK  {name}")
