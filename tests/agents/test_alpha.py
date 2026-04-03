from __future__ import annotations

import unittest
from unittest.mock import patch

from sepa.agents.alpha import AlphaScreener


class AlphaScreenerTest(unittest.TestCase):
    def _make_closes(self, length: int = 300, base: float = 10000.0, trend: float = 1.001) -> list[dict]:
        closes = []
        price = base
        for i in range(length):
            price *= trend
            closes.append({'close': round(price, 2), 'volume': 100000})
        return closes

    @patch('sepa.agents.alpha.get_symbol_name', return_value='테스트종목')
    @patch('sepa.agents.alpha.read_price_series_from_path')
    def test_strong_uptrend_passes_all_checks(self, mock_read, mock_name):
        mock_read.return_value = self._make_closes(300, base=5000, trend=1.003)
        from pathlib import Path
        screener = AlphaScreener(data_dir=Path('/tmp/fake'), top_n=10)
        with patch.object(screener, '_iter_csv_files', return_value=[Path('/tmp/fake/005930.KS.csv')]):
            results = screener.run()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['symbol'], '005930.KS')
        self.assertTrue(all(results[0]['checks'].values()))

    @patch('sepa.agents.alpha.get_symbol_name', return_value='테스트')
    @patch('sepa.agents.alpha.read_price_series_from_path')
    def test_insufficient_history_excluded(self, mock_read, mock_name):
        mock_read.return_value = self._make_closes(100)
        from pathlib import Path
        screener = AlphaScreener(data_dir=Path('/tmp/fake'), top_n=10)
        with patch.object(screener, '_iter_csv_files', return_value=[Path('/tmp/fake/TEST.csv')]):
            results = screener.run()

        self.assertEqual(len(results), 0)

    def test_percentile_map_single_item(self):
        result = AlphaScreener._percentile_map({'A': 0.5})
        self.assertEqual(result['A'], 100.0)

    def test_percentile_map_multiple_items(self):
        result = AlphaScreener._percentile_map({'A': 0.1, 'B': 0.5, 'C': 0.9})
        self.assertAlmostEqual(result['A'], 0.0)
        self.assertAlmostEqual(result['B'], 50.0)
        self.assertAlmostEqual(result['C'], 100.0)


if __name__ == '__main__':
    unittest.main()
