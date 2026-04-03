"""Tests for sepa.scoring.factors — pure factor functions."""
import pytest
from sepa.scoring.factors import (
    breadth_above_ma,
    earnings_proxy,
    near_52w_high,
    near_high_ratio,
    rs_relative,
    to_percentile,
    trend_template_ratio,
    turnover_trend,
    volatility_contraction,
    volume_expansion,
)


def _rising(n=300, start=100.0, step=0.5):
    return [start + i * step for i in range(n)]


def _flat(n=300, value=100.0):
    return [value] * n


class TestRsRelative:
    def test_outperform(self):
        asset = _rising(300, 100, 1.0)  # strong uptrend
        bench = _flat(300, 100.0)
        rs = rs_relative(asset, bench, 20)
        assert rs > 0

    def test_underperform(self):
        asset = _flat(300, 100.0)
        bench = _rising(300, 100, 1.0)
        rs = rs_relative(asset, bench, 20)
        assert rs < 0

    def test_short_data(self):
        assert rs_relative([100, 110], [100, 105], 20) == 0.0


class TestBreadthAboveMa:
    def test_all_above(self):
        stocks = [_rising(60)] * 10
        assert breadth_above_ma(stocks, window=50) == 1.0

    def test_none_above(self):
        stocks = [list(reversed(_rising(60)))] * 10  # declining
        assert breadth_above_ma(stocks, window=50) == 0.0

    def test_empty(self):
        assert breadth_above_ma([], window=50) == 0.0


class TestNearHighRatio:
    def test_at_highs(self):
        stocks = [_rising(260)] * 10  # all at 52w highs
        assert near_high_ratio(stocks) == 1.0

    def test_far_from_highs(self):
        # Peaks at 200, now at 100 — below 80% threshold
        series = _rising(130, 100, 1.0) + list(reversed(_rising(130, 100, 1.0)))
        stocks = [series] * 10
        assert near_high_ratio(stocks) < 0.5


class TestTurnoverTrend:
    def test_increasing(self):
        vols = [100] * 60 + [200] * 20
        assert turnover_trend(vols) > 1.0

    def test_decreasing(self):
        vols = [200] * 60 + [100] * 20
        assert turnover_trend(vols) < 1.0

    def test_short_data(self):
        assert turnover_trend([100] * 10) == 1.0


class TestTrendTemplateRatio:
    def test_all_pass(self):
        checks = {f'c{i}': True for i in range(8)}
        assert trend_template_ratio(checks) == 1.0

    def test_five_pass(self):
        checks = {f'c{i}': i < 5 for i in range(8)}
        assert trend_template_ratio(checks) == 5 / 8

    def test_empty(self):
        assert trend_template_ratio({}) == 0.0


class TestNear52wHigh:
    def test_at_high(self):
        closes = _rising(260)
        assert near_52w_high(closes) == pytest.approx(1.0, abs=0.01)

    def test_half_of_high(self):
        closes = _rising(130) + _flat(130, 65)
        ratio = near_52w_high(closes)
        assert 0.0 < ratio < 0.6


class TestVolumeExpansion:
    def test_expanding(self):
        vols = [100.0] * 50 + [300.0] * 5
        assert volume_expansion(vols) > 0.5

    def test_contracting(self):
        vols = [300.0] * 50 + [100.0] * 5
        assert volume_expansion(vols) < 0.5


class TestVolatilityContraction:
    def test_contracting(self):
        # Wide swings then narrow
        closes = [100 + (i % 10) * 3 for i in range(40)] + [100 + (i % 10) * 0.5 for i in range(20)]
        vc = volatility_contraction(closes, short=10, long=40)
        assert vc > 0.0

    def test_short_data(self):
        assert volatility_contraction([100] * 10) == 0.5


class TestEarningsProxy:
    def test_with_eps(self):
        ep = earnings_proxy(eps_yoy=0.30, roe=20.0, opm=15.0)
        assert 0.0 <= ep <= 1.0

    def test_no_data(self):
        assert earnings_proxy() == 0.5

    def test_turnover_fallback(self):
        ep = earnings_proxy(turnover_accel=1.5)
        assert 0.0 < ep < 1.0


class TestToPercentile:
    def test_three_items(self):
        result = to_percentile({'a': 10, 'b': 20, 'c': 30})
        assert result['a'] == 0.0
        assert result['c'] == 1.0

    def test_single_item(self):
        result = to_percentile({'x': 5})
        assert result['x'] == 1.0
