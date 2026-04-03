"""Tests for sepa.scoring.leader_stock."""
from sepa.scoring.leader_stock import score_stocks


def _make_stock(symbol='005930', passes=8):
    checks = {f'c{i}': i < passes for i in range(8)}
    return {
        'symbol': symbol,
        'name': 'Test Stock',
        'sector': 'Tech',
        'closes': [100 + i * 0.5 for i in range(300)],
        'volumes': [1000000.0] * 300,
        'checks': checks,
        'rs_percentile': 80.0,
    }


class TestScoreStocks:
    def test_basic_scoring(self):
        stocks = [_make_stock('A', 8), _make_stock('B', 6), _make_stock('C', 7)]
        results = score_stocks(stocks)
        assert len(results) == 3
        for r in results:
            assert 0.0 <= r['leader_score'] <= 1.0
            assert 'rs_120_pct' in r
            assert 'trend_template_score' in r
            assert 'reason' in r

    def test_gate_tt_below_5(self):
        stocks = [_make_stock('A', 4)]  # only 4/8 pass
        results = score_stocks(stocks, min_tt_pass=5)
        assert len(results) == 0

    def test_gate_close_below_ma50(self):
        stock = _make_stock('A', 8)
        # Make last close below MA50
        stock['closes'] = [200 - i * 0.5 for i in range(300)]  # declining
        results = score_stocks([stock])
        assert len(results) == 0

    def test_sorted_by_score(self):
        stocks = [_make_stock(f'S{i}', 8) for i in range(5)]
        # Give different RS to create different scores
        for i, s in enumerate(stocks):
            s['rs_percentile'] = 50.0 + i * 10
        results = score_stocks(stocks)
        scores = [r['leader_score'] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty(self):
        assert score_stocks([]) == []
