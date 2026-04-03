"""Base classes and data models for Market Wizards strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


# ---------------------------------------------------------------------------
# Input data model — one stock's full data packet
# ---------------------------------------------------------------------------

@dataclass
class StockData:
    """Standardised input for every wizard strategy screen."""

    symbol: str
    closes: list[float] = field(default_factory=list)
    highs: list[float] = field(default_factory=list)
    lows: list[float] = field(default_factory=list)
    volumes: list[float] = field(default_factory=list)

    # Fundamentals (optional — NaN means not available)
    per: float = float('nan')
    pbr: float = float('nan')
    roe: float = float('nan')
    eps_yoy: float = float('nan')          # EPS year-over-year growth %
    eps_qoq: float = float('nan')          # EPS quarter-over-quarter growth %
    eps_acceleration: float = float('nan')  # Change in growth rate
    revenue_growth: float = float('nan')    # Revenue YoY %
    debt_ratio: float = float('nan')        # 부채비율 %
    market_cap: float = float('nan')        # 시가총액 (억원)

    # Sector context
    sector: str = ''
    sector_avg_per: float = float('nan')
    sector_index_change_5d: float = float('nan')  # 업종지수 5일 등락률
    sector_index_above_ma50: bool = True

    # Foreign / institutional flow (optional)
    foreign_net_buy_5d: float = 0.0  # 외국인 5일 순매수

    @property
    def close(self) -> float:
        return self.closes[-1] if self.closes else 0.0

    @property
    def high(self) -> float:
        return self.highs[-1] if self.highs else 0.0

    @property
    def low(self) -> float:
        return self.lows[-1] if self.lows else 0.0

    @property
    def volume(self) -> float:
        return self.volumes[-1] if self.volumes else 0.0

    @property
    def prev_close(self) -> float:
        return self.closes[-2] if len(self.closes) >= 2 else 0.0

    @property
    def prev_high(self) -> float:
        return self.highs[-2] if len(self.highs) >= 2 else 0.0

    @property
    def daily_change_pct(self) -> float:
        if self.prev_close:
            return (self.close - self.prev_close) / self.prev_close * 100.0
        return 0.0

    @property
    def daily_turnover(self) -> float:
        """거래대금 (억원 추정 = 종가 × 거래량 / 1e8)."""
        return self.close * self.volume / 1e8 if self.close and self.volume else 0.0


# ---------------------------------------------------------------------------
# Condition result — one condition within a strategy
# ---------------------------------------------------------------------------

@dataclass
class ConditionResult:
    """Single condition evaluation."""
    name: str            # e.g. "현재가 > SMA200"
    passed: bool
    actual: str = ''     # e.g. "15,200 vs 14,800"
    kiwoom_expr: str = ''  # 키움 조건식 표현


# ---------------------------------------------------------------------------
# Strategy screening result
# ---------------------------------------------------------------------------

@dataclass
class WizardResult:
    """Output from a single wizard strategy screen on one stock."""

    strategy_name: str
    trader: str
    category: str            # trend_following, growth_momentum, swing, contrarian_value, volatility_contraction, macro_liquidity
    symbol: str
    passed: bool             # 전체 통과 여부
    score: float             # 0-100 종합 점수
    conditions: list[ConditionResult] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        if not self.conditions:
            return 0.0
        return sum(1 for c in self.conditions if c.passed) / len(self.conditions) * 100.0

    @property
    def conditions_met(self) -> int:
        return sum(1 for c in self.conditions if c.passed)

    @property
    def conditions_total(self) -> int:
        return len(self.conditions)


# ---------------------------------------------------------------------------
# Base strategy class
# ---------------------------------------------------------------------------

class WizardStrategy:
    """Abstract base for all Market Wizards strategies.

    Subclasses MUST implement:
      - name, trader, category (class attributes)
      - screen(data: StockData) -> WizardResult

    Optionally override:
      - kiwoom_conditions() -> list[str]  — human-readable 키움 조건식
      - description() -> str
    """

    name: str = ''
    trader: str = ''
    category: str = ''
    book: str = ''         # 'MW1989', 'NMW1992', 'SMW2001'
    description_text: str = ''

    def screen(self, data: StockData) -> WizardResult:
        raise NotImplementedError

    def kiwoom_conditions(self) -> list[str]:
        """Return list of 키움 HTS 조건식 표현 strings."""
        return []

    def _result(
        self,
        symbol: str,
        conditions: list[ConditionResult],
        *,
        require_all: bool = True,
        metadata: dict | None = None,
    ) -> WizardResult:
        """Helper to build WizardResult from condition list."""
        if require_all:
            passed = all(c.passed for c in conditions)
        else:
            passed = sum(c.passed for c in conditions) >= len(conditions) * 0.7

        # Score: base on pass rate, bonus for all-pass
        pass_pct = sum(c.passed for c in conditions) / len(conditions) if conditions else 0.0
        score = round(pass_pct * 80.0 + (20.0 if passed else 0.0), 1)

        return WizardResult(
            strategy_name=self.name,
            trader=self.trader,
            category=self.category,
            symbol=symbol,
            passed=passed,
            score=score,
            conditions=conditions,
            metadata=metadata or {},
        )

    @staticmethod
    def _cond(name: str, passed: bool, actual: str = '', kiwoom: str = '') -> ConditionResult:
        return ConditionResult(name=name, passed=passed, actual=actual, kiwoom_expr=kiwoom)

    @staticmethod
    def _safe_nan(v: float) -> bool:
        """True if v is NaN or inf."""
        try:
            return v != v or abs(v) == float('inf')
        except (TypeError, ValueError):
            return True
