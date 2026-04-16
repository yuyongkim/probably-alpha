"""Tests for Market Wizards strategy screener."""

from __future__ import annotations

import math
import pytest

from sepa.wizards import (
    StockData,
    WizardScreener,
    ALL_STRATEGIES,
    DennisTurtleSystem1,
    MinerviniTrendTemplate,
    SchwartzEma10,
    RogersDeepValue,
    ONeilCanSlim,
    TroutMeanReversion,
    GalanteShortSetup,
)
from sepa.wizards.indicators import rsi, ema, sma, bollinger_bands, atr, adx, nr7
from sepa.wizards.kiwoom_export import KiwoomExporter
from sepa.backtest.presets import CLUSTER_PERSON_PRESET_MAP, PERSON_PRESET_MAP, list_presets


# ---------------------------------------------------------------------------
# Fixtures: synthetic price data
# ---------------------------------------------------------------------------

def _uptrend_stock(symbol: str = '005930.KS') -> StockData:
    """Generate a strong uptrend stock (300 bars)."""
    n = 300
    base = 10000
    closes = [base + i * 50 + (i % 5) * 10 for i in range(n)]
    highs = [c + 200 for c in closes]
    lows = [c - 150 for c in closes]
    volumes = [1_000_000 + (i % 10) * 50_000 for i in range(n)]
    # Last bar: strong day with high volume
    closes[-1] = closes[-2] * 1.04
    highs[-1] = closes[-1] + 100
    lows[-1] = closes[-1] - 50
    volumes[-1] = 3_000_000

    return StockData(
        symbol=symbol,
        closes=closes,
        highs=highs,
        lows=lows,
        volumes=volumes,
        per=12.0,
        pbr=1.5,
        roe=18.0,
        eps_yoy=30.0,
        eps_qoq=28.0,
        revenue_growth=20.0,
        debt_ratio=80.0,
        market_cap=5000.0,
        sector='반도체',
        sector_avg_per=20.0,
        foreign_net_buy_5d=100_000,
    )


def _downtrend_stock(symbol: str = '000660.KS') -> StockData:
    """Generate a downtrend stock."""
    n = 300
    base = 50000
    closes = [base - i * 80 for i in range(n)]
    closes = [max(c, 1000) for c in closes]
    highs = [c + 300 for c in closes]
    lows = [c - 200 for c in closes]
    volumes = [500_000 + (i % 7) * 30_000 for i in range(n)]

    return StockData(
        symbol=symbol,
        closes=closes,
        highs=highs,
        lows=lows,
        volumes=volumes,
        per=50.0,
        pbr=3.0,
        eps_yoy=-10.0,
        sector_avg_per=20.0,
    )


def _value_stock(symbol: str = '003490.KS') -> StockData:
    """Generate an undervalued stock near 52-week low."""
    n = 300
    closes = [20000 - i * 30 for i in range(n)]
    closes = [max(c, 5000) for c in closes]
    # Small uptick at the end
    for i in range(5):
        closes[-(i + 1)] = closes[-6] + (5 - i) * 50
    highs = [c + 100 for c in closes]
    lows = [c - 80 for c in closes]
    volumes = [100_000] * n
    volumes[-1] = 200_000

    return StockData(
        symbol=symbol,
        closes=closes,
        highs=highs,
        lows=lows,
        volumes=volumes,
        per=4.0,
        pbr=0.5,
        roe=8.0,
        debt_ratio=60.0,
        revenue_growth=5.0,
        sector_avg_per=15.0,
    )


# ---------------------------------------------------------------------------
# Indicator tests
# ---------------------------------------------------------------------------

class TestIndicators:

    def test_rsi_length(self):
        closes = list(range(100, 150))
        result = rsi(closes, 14)
        assert len(result) == len(closes)
        # First 14 should be NaN
        assert math.isnan(result[0])
        # After period, should be valid
        assert not math.isnan(result[14])

    def test_rsi_bounds(self):
        closes = list(range(100, 200))
        result = rsi(closes, 14)
        for v in result:
            if not math.isnan(v):
                assert 0 <= v <= 100

    def test_ema_basic(self):
        values = [10.0] * 20
        result = ema(values, 10)
        assert len(result) == 20
        assert abs(result[-1] - 10.0) < 0.001

    def test_sma_basic(self):
        values = [10.0] * 20
        result = sma(values, 5)
        assert abs(result[-1] - 10.0) < 0.001
        assert math.isnan(result[0])

    def test_bollinger_bands(self):
        closes = [100.0 + (i % 3) for i in range(30)]
        upper, middle, lower, bw = bollinger_bands(closes, 20, 2.0)
        assert len(upper) == 30
        assert not math.isnan(upper[-1])
        assert upper[-1] > middle[-1] > lower[-1]

    def test_atr_basic(self):
        highs = [105.0] * 30
        lows = [95.0] * 30
        closes = [100.0] * 30
        result = atr(highs, lows, closes, 14)
        assert len(result) == 30
        assert not math.isnan(result[-1])
        assert result[-1] == pytest.approx(10.0, abs=0.5)

    def test_nr7(self):
        highs = [110, 109, 108, 107, 106, 105, 104, 103]
        lows = [100, 101, 102, 103, 104, 103, 103, 102.5]
        result = nr7(highs, lows)
        assert len(result) == 8
        # Last bar range = 103-102.5 = 0.5 — should be narrowest
        assert result[-1] is True


# ---------------------------------------------------------------------------
# Strategy tests
# ---------------------------------------------------------------------------

class TestStrategies:

    def test_all_strategies_have_metadata(self):
        for cls in ALL_STRATEGIES:
            assert cls.name, f'{cls} missing name'
            assert cls.trader, f'{cls} missing trader'
            assert cls.category, f'{cls} missing category'
            assert cls.book, f'{cls} missing book'

    def test_all_strategies_can_screen(self):
        stock = _uptrend_stock()
        for cls in ALL_STRATEGIES:
            strategy = cls()
            result = strategy.screen(stock)
            assert result.symbol == stock.symbol
            assert result.strategy_name == cls.name
            assert len(result.conditions) > 0

    def test_all_strategies_have_kiwoom_conditions(self):
        for cls in ALL_STRATEGIES:
            instance = cls()
            conds = instance.kiwoom_conditions()
            assert len(conds) > 0, f'{cls.name} has no kiwoom conditions'

    def test_uptrend_passes_trend_following(self):
        stock = _uptrend_stock()
        result = DennisTurtleSystem1().screen(stock)
        # Uptrend should pass most conditions
        assert result.conditions_met >= 2

    def test_minervini_trend_template(self):
        stock = _uptrend_stock()
        result = MinerviniTrendTemplate().screen(stock)
        assert result.conditions_total == 8
        assert result.score > 0

    def test_schwartz_ema10(self):
        stock = _uptrend_stock()
        result = SchwartzEma10().screen(stock)
        assert result.conditions_total == 4

    def test_rogers_value_on_value_stock(self):
        stock = _value_stock()
        result = RogersDeepValue().screen(stock)
        # Value stock should pass PBR and PER conditions
        pbr_cond = [c for c in result.conditions if 'PBR' in c.name]
        assert pbr_cond and pbr_cond[0].passed

    def test_galante_short_on_downtrend(self):
        stock = _downtrend_stock()
        result = GalanteShortSetup().screen(stock)
        assert result.metadata.get('direction') == 'short'

    def test_trout_mean_reversion_conditions(self):
        stock = _uptrend_stock()
        result = TroutMeanReversion().screen(stock)
        # Uptrend should NOT pass mean reversion (needs oversold)
        assert not result.passed


# ---------------------------------------------------------------------------
# Screener tests
# ---------------------------------------------------------------------------

class TestScreener:

    def test_screener_all_strategies(self):
        screener = WizardScreener()
        assert screener.strategy_count == len(ALL_STRATEGIES)

    def test_screener_filter_category(self):
        screener = WizardScreener(categories=['swing'])
        assert screener.strategy_count == 4

    def test_screener_filter_trader(self):
        screener = WizardScreener(traders=['Mark Minervini'])
        assert screener.strategy_count == 2  # TT + VCP

    def test_screen_universe(self):
        stocks = [_uptrend_stock(), _downtrend_stock(), _value_stock()]
        screener = WizardScreener()
        results = screener.screen_universe(stocks)
        assert len(results) == 3
        # Results should be sorted by strategies_passed desc
        assert results[0].strategies_passed >= results[-1].strategies_passed

    def test_passed_only(self):
        stocks = [_uptrend_stock(), _downtrend_stock()]
        screener = WizardScreener()
        results = screener.screen_universe(stocks)
        passed = screener.passed_only(results, min_strategies=3)
        for r in passed:
            assert r.strategies_passed >= 3

    def test_summary(self):
        stocks = [_uptrend_stock()]
        screener = WizardScreener()
        results = screener.screen_universe(stocks)
        summary = screener.summary(results)
        assert summary['total_stocks_screened'] == 1
        assert summary['total_strategies'] == len(ALL_STRATEGIES)
        assert 'strategy_hit_rates' in summary

    def test_available_strategies(self):
        info = WizardScreener.available_strategies()
        assert len(info) == len(ALL_STRATEGIES)
        for item in info:
            assert 'name' in item
            assert 'kiwoom_conditions' in item

    def test_screen_result_to_dict(self):
        stock = _uptrend_stock()
        screener = WizardScreener()
        result = screener.screen_stock(stock)
        d = result.to_dict()
        assert d['symbol'] == stock.symbol
        assert 'details' in d
        assert len(d['details']) == screener.strategy_count


# ---------------------------------------------------------------------------
# Kiwoom Export tests
# ---------------------------------------------------------------------------

class TestKiwoomExport:

    def test_export_all(self):
        exporter = KiwoomExporter()
        result = exporter.export_all()
        assert len(result) == len(ALL_STRATEGIES)

    def test_export_by_category(self):
        exporter = KiwoomExporter()
        result = exporter.export_by_category('trend_following')
        assert len(result) > 0
        for item in result:
            assert item['category'] == 'trend_following'

    def test_export_by_trader(self):
        exporter = KiwoomExporter()
        result = exporter.export_by_trader('Mark Minervini')
        assert len(result) == 2

    def test_to_text(self):
        exporter = KiwoomExporter()
        text = exporter.to_text()
        assert '추세추종' in text
        assert 'Richard Dennis' in text
        assert 'Mark Minervini' in text

    def test_save_json(self, tmp_path):
        exporter = KiwoomExporter()
        path = tmp_path / 'kiwoom.json'
        exporter.save_json(path)
        assert path.exists()
        import json
        data = json.loads(path.read_text(encoding='utf-8'))
        assert data['total_strategies'] == len(ALL_STRATEGIES)
        assert 'combined_conditions' in data


class TestPresetPersonMappings:

    def test_all_promoted_aliases_are_available_in_person_map(self):
        sample_ids = [
            'jim-rogers',
            'al-weiss',
            'tony-saliba',
            'blair-hull',
            'randy-mckay',
            'buddy-fletcher',
            'steve-lescarbeau',
            'john-bender',
            'tom-baldwin',
            'bruce-gelber',
            'mark-ritchie',
            'jeffrey-neumann',
        ]
        for person_id in sample_ids:
            assert person_id in PERSON_PRESET_MAP

    def test_cluster_map_is_retired_after_full_promotion(self):
        assert CLUSTER_PERSON_PRESET_MAP == {}

    def test_backtest_preset_api_payload_includes_runtime_conditions(self):
        presets = list_presets()
        oneil = next(item for item in presets if item['id'] == 'oneil')
        assert oneil['runtime_conditions']
        assert any('EPS YoY' in line for line in oneil['runtime_conditions'])
        assert 'Close >= 52W High x 0.75' in oneil['runtime_conditions']
        assert 'EPS QoQ >= 25%' in oneil['runtime_conditions']

    def test_okumus_runtime_conditions_match_deep_value_turnaround(self):
        presets = list_presets()
        okumus = next(item for item in presets if item['id'] == 'okumus')
        assert 'PER <= 8.0' in okumus['runtime_conditions']
        assert 'PBR <= 0.7' in okumus['runtime_conditions']
        assert 'Debt ratio <= 100%' in okumus['runtime_conditions']
        assert 'Close <= 52W High x 0.50' in okumus['runtime_conditions']
        assert '5D return > 0%' in okumus['runtime_conditions']
