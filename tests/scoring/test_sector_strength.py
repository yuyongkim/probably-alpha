"""Tests for sepa.scoring.sector_strength."""
from sepa.scoring.sector_strength import score_sectors


def _make_stock(n=300, base=100, trend=0.5):
    closes = [base + i * trend for i in range(n)]
    volumes = [1000000.0] * n
    return {'closes': closes, 'volumes': volumes}


class TestScoreSectors:
    def test_basic_scoring(self):
        sector_data = {
            'Tech': [_make_stock(trend=1.0) for _ in range(10)],
            'Energy': [_make_stock(trend=0.2) for _ in range(8)],
        }
        benchmark = [100 + i * 0.5 for i in range(300)]
        results = score_sectors(sector_data, benchmark)
        assert len(results) == 2
        assert results[0]['sector_score'] >= results[1]['sector_score']
        for r in results:
            assert 0.0 <= r['sector_score'] <= 1.0
            assert 'rs_20' in r
            assert 'breadth_50ma' in r
            assert 'stock_count' in r

    def test_excludes_small_sectors(self):
        sector_data = {
            'Big': [_make_stock() for _ in range(10)],
            'Tiny': [_make_stock() for _ in range(3)],  # < 5
        }
        benchmark = [100] * 300
        results = score_sectors(sector_data, benchmark)
        sectors = [r['sector'] for r in results]
        assert 'Tiny' not in sectors

    def test_empty_input(self):
        assert score_sectors({}, [100] * 300) == []
