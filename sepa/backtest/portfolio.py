"""Portfolio tracking for backtests.

Tracks positions, cash, trade log, and daily equity curve.
Per docs/20_architecture/BACKTEST_RULES.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Trade:
    symbol: str
    side: str  # 'buy' or 'sell'
    date: str
    price: float
    qty: int
    cost: float  # total cost after commission+slippage+tax
    reason: str = ''


@dataclass
class Position:
    symbol: str
    entry_date: str
    entry_price: float
    qty: int
    stop: float
    sector: str = ''


class Portfolio:
    """Simple portfolio tracker with cost model.

    Cost model (per BACKTEST_RULES.md section 2):
    - Commission: 0.015% per side
    - Slippage: 0.1% (base)
    - Tax: 0.18% on sells only
    """

    COMMISSION_RATE = 0.00015
    SLIPPAGE_RATE = 0.001
    TAX_RATE = 0.0018

    def __init__(self, initial_cash: float = 100_000_000.0, max_positions: int = 10) -> None:
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.max_positions = max_positions
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.equity_curve: list[dict] = []  # [{date, equity, cash, positions_value}]

    def buy(self, symbol: str, date_str: str, price: float, sector: str = '', stop: float = 0.0) -> bool:
        if symbol in self.positions:
            return False
        if len(self.positions) >= self.max_positions:
            return False

        # Position sizing: equal weight
        target_value = self.cash / max(1, self.max_positions - len(self.positions))
        target_value = min(target_value, self.cash * 0.95)  # keep 5% buffer

        # Apply buy costs
        effective_price = price * (1.0 + self.SLIPPAGE_RATE)
        cost_per_share = effective_price * (1.0 + self.COMMISSION_RATE)
        qty = int(target_value / cost_per_share) if cost_per_share > 0 else 0
        if qty <= 0:
            return False

        total_cost = int(qty * cost_per_share)
        if total_cost > self.cash:
            qty = int(self.cash / cost_per_share)
            total_cost = int(qty * cost_per_share)
        if qty <= 0:
            return False

        self.cash -= total_cost
        if stop <= 0:
            stop = price * 0.925  # default 7.5% stop

        self.positions[symbol] = Position(
            symbol=symbol,
            entry_date=date_str,
            entry_price=price,
            qty=qty,
            stop=stop,
            sector=sector,
        )
        self.trades.append(Trade(
            symbol=symbol, side='buy', date=date_str,
            price=effective_price, qty=qty, cost=total_cost, reason='signal',
        ))
        return True

    def sell(self, symbol: str, date_str: str, price: float, reason: str = 'signal') -> float | None:
        pos = self.positions.pop(symbol, None)
        if pos is None:
            return None

        effective_price = price * (1.0 - self.SLIPPAGE_RATE)
        gross = pos.qty * effective_price
        commission = gross * self.COMMISSION_RATE
        tax = gross * self.TAX_RATE
        net = gross - commission - tax

        self.cash += int(net)
        pnl = int(net) - int(pos.qty * pos.entry_price * (1.0 + self.SLIPPAGE_RATE) * (1.0 + self.COMMISSION_RATE))

        self.trades.append(Trade(
            symbol=symbol, side='sell', date=date_str,
            price=effective_price, qty=pos.qty, cost=net, reason=reason,
        ))
        return pnl

    def mark_to_market(self, date_str: str, prices: dict[str, float]) -> float:
        """Record daily equity. Returns total equity."""
        positions_value = sum(
            pos.qty * prices.get(pos.symbol, pos.entry_price)
            for pos in self.positions.values()
        )
        equity = int(self.cash + positions_value)
        # Skip if no valid prices (non-trading day)
        if self.positions and positions_value == 0:
            return self.equity_curve[-1]['equity'] if self.equity_curve else equity
        self.equity_curve.append({
            'date': date_str,
            'equity': equity,
            'cash': int(self.cash),
            'positions_value': int(positions_value),
            'num_positions': len(self.positions),
        })
        return equity

    def check_stops(self, date_str: str, prices: dict[str, float]) -> list[str]:
        """Check stop-losses. Returns list of symbols sold."""
        stopped: list[str] = []
        for symbol in list(self.positions):
            price = prices.get(symbol, 0.0)
            if price <= 0:
                continue
            if price <= self.positions[symbol].stop:
                self.sell(symbol, date_str, price, reason='stop_loss')
                stopped.append(symbol)
        return stopped
