"""Unified screener that runs all Market Wizards strategies against a stock universe.

Usage:
    from sepa.wizards.screener import WizardScreener

    screener = WizardScreener()                          # all strategies
    screener = WizardScreener(categories=['swing'])       # only swing
    screener = WizardScreener(traders=['Mark Minervini']) # specific trader

    results = screener.screen_universe(stocks)
    passed  = screener.passed_only(results)
    report  = screener.summary(results)
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Sequence

from sepa.wizards.base import StockData, WizardResult, WizardStrategy
from sepa.wizards.trend_followers import ALL_TREND_FOLLOWERS
from sepa.wizards.growth_momentum import ALL_GROWTH_MOMENTUM
from sepa.wizards.swing_traders import ALL_SWING_TRADERS
from sepa.wizards.contrarian_value import ALL_CONTRARIAN_VALUE
from sepa.wizards.volatility_macro import ALL_VOLATILITY_MACRO


# ---------------------------------------------------------------------------
# Full registry
# ---------------------------------------------------------------------------

ALL_STRATEGIES: list[type[WizardStrategy]] = (
    ALL_TREND_FOLLOWERS
    + ALL_GROWTH_MOMENTUM
    + ALL_SWING_TRADERS
    + ALL_CONTRARIAN_VALUE
    + ALL_VOLATILITY_MACRO
)

CATEGORY_MAP: dict[str, list[type[WizardStrategy]]] = {
    'trend_following': ALL_TREND_FOLLOWERS,
    'growth_momentum': ALL_GROWTH_MOMENTUM,
    'swing': ALL_SWING_TRADERS,
    'contrarian_value': ALL_CONTRARIAN_VALUE,
    'volatility_contraction': [
        s for s in ALL_VOLATILITY_MACRO
        if s.category == 'volatility_contraction'
    ],
    'macro_liquidity': [
        s for s in ALL_VOLATILITY_MACRO
        if s.category == 'macro_liquidity'
    ],
}


# ---------------------------------------------------------------------------
# Screener
# ---------------------------------------------------------------------------

@dataclass
class ScreenResult:
    """Aggregated result for one stock across all strategies."""
    symbol: str
    results: list[WizardResult] = field(default_factory=list)

    @property
    def strategies_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def strategies_total(self) -> int:
        return len(self.results)

    @property
    def best_score(self) -> float:
        return max((r.score for r in self.results), default=0.0)

    @property
    def avg_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.score for r in self.results) / len(self.results)

    @property
    def passed_strategies(self) -> list[str]:
        return [r.strategy_name for r in self.results if r.passed]

    @property
    def passed_traders(self) -> list[str]:
        return list(dict.fromkeys(r.trader for r in self.results if r.passed))

    @property
    def passed_categories(self) -> list[str]:
        return list(dict.fromkeys(r.category for r in self.results if r.passed))

    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'strategies_passed': self.strategies_passed,
            'strategies_total': self.strategies_total,
            'best_score': self.best_score,
            'avg_score': round(self.avg_score, 1),
            'passed_strategies': self.passed_strategies,
            'passed_traders': self.passed_traders,
            'passed_categories': self.passed_categories,
            'details': [
                {
                    'strategy': r.strategy_name,
                    'trader': r.trader,
                    'category': r.category,
                    'passed': r.passed,
                    'score': r.score,
                    'conditions_met': r.conditions_met,
                    'conditions_total': r.conditions_total,
                    'conditions': [
                        {
                            'name': c.name,
                            'passed': c.passed,
                            'actual': c.actual,
                            'kiwoom_expr': c.kiwoom_expr,
                        }
                        for c in r.conditions
                    ],
                    'metadata': r.metadata,
                }
                for r in self.results
            ],
        }


class WizardScreener:
    """Run selected wizard strategies against a stock universe."""

    def __init__(
        self,
        *,
        categories: list[str] | None = None,
        traders: list[str] | None = None,
        strategy_names: list[str] | None = None,
    ) -> None:
        strategies = ALL_STRATEGIES

        if categories:
            cat_set = set(categories)
            strategies = [s for s in strategies if s.category in cat_set]

        if traders:
            trader_set = {t.lower() for t in traders}
            strategies = [s for s in strategies if s.trader.lower() in trader_set]

        if strategy_names:
            name_set = {n.lower() for n in strategy_names}
            strategies = [s for s in strategies if s.name.lower() in name_set]

        self._strategy_classes = strategies
        self._instances: list[WizardStrategy] = [cls() for cls in strategies]

    @property
    def strategy_count(self) -> int:
        return len(self._instances)

    @property
    def strategy_names(self) -> list[str]:
        return [s.name for s in self._instances]

    def screen_stock(self, data: StockData) -> ScreenResult:
        """Run all selected strategies on one stock."""
        result = ScreenResult(symbol=data.symbol)
        for strategy in self._instances:
            result.results.append(strategy.screen(data))
        return result

    def screen_universe(self, stocks: list[StockData]) -> list[ScreenResult]:
        """Run all strategies on all stocks. Returns list sorted by best_score desc."""
        results = [self.screen_stock(stock) for stock in stocks]
        results.sort(key=lambda r: (-r.strategies_passed, -r.best_score))
        return results

    def passed_only(
        self,
        results: list[ScreenResult],
        min_strategies: int = 1,
    ) -> list[ScreenResult]:
        """Filter to stocks that passed at least N strategies."""
        return [r for r in results if r.strategies_passed >= min_strategies]

    def summary(self, results: list[ScreenResult]) -> dict:
        """Generate a summary report."""
        total_stocks = len(results)
        passed_any = sum(1 for r in results if r.strategies_passed > 0)

        # Strategy hit rates
        strategy_hits: dict[str, int] = defaultdict(int)
        for r in results:
            for wr in r.results:
                if wr.passed:
                    strategy_hits[wr.strategy_name] += 1

        # Category distribution
        cat_hits: dict[str, int] = defaultdict(int)
        for r in results:
            for cat in r.passed_categories:
                cat_hits[cat] += 1

        # Top stocks
        top_stocks = [
            {
                'symbol': r.symbol,
                'strategies_passed': r.strategies_passed,
                'best_score': r.best_score,
                'passed_strategies': r.passed_strategies,
            }
            for r in sorted(results, key=lambda x: (-x.strategies_passed, -x.best_score))[:20]
            if r.strategies_passed > 0
        ]

        return {
            'total_stocks_screened': total_stocks,
            'stocks_passing_any': passed_any,
            'total_strategies': self.strategy_count,
            'strategy_hit_rates': dict(
                sorted(strategy_hits.items(), key=lambda x: -x[1])
            ),
            'category_distribution': dict(
                sorted(cat_hits.items(), key=lambda x: -x[1])
            ),
            'top_stocks': top_stocks,
        }

    @staticmethod
    def available_strategies() -> list[dict]:
        """List all available strategies with metadata."""
        return [
            {
                'name': cls.name,
                'trader': cls.trader,
                'category': cls.category,
                'book': cls.book,
                'description': cls.description_text,
                'kiwoom_conditions': cls().kiwoom_conditions(),
            }
            for cls in ALL_STRATEGIES
        ]

    @staticmethod
    def available_categories() -> list[str]:
        return list(CATEGORY_MAP.keys())

    @staticmethod
    def available_traders() -> list[str]:
        return list(dict.fromkeys(cls.trader for cls in ALL_STRATEGIES))
