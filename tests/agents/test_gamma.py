from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


class GammaResearcherTest(unittest.TestCase):
    @patch('sepa.agents.gamma.read_company_snapshot', return_value={'roe': 22.0, 'opm': 18.0})
    @patch('sepa.agents.gamma.MacroDataProvider')
    @patch('sepa.agents.gamma.DartProvider')
    def test_run_basic_scoring(self, mock_dart_cls, mock_macro_cls, mock_snapshot):
        mock_macro = MagicMock()
        mock_macro.get_snapshot.return_value = {'wti': 70.0, 'fred_pmi_proxy': None, 'ecos_rate': None}
        mock_macro_cls.return_value = mock_macro

        mock_dart = MagicMock()
        mock_dart.get_growth_hint.return_value = {
            'growth_hint': 1.5,
            'status': 'strong_growth',
            'latest_yoy': 0.25,
            'acceleration': 0.05,
        }
        mock_dart_cls.return_value = mock_dart

        from sepa.agents.gamma import GammaResearcher
        researcher = GammaResearcher()
        result = researcher.run([
            {'symbol': '005930.KS', 'confidence': 7.0},
        ])

        self.assertIn('general', result)
        self.assertEqual(len(result['general']), 1)
        item = result['general'][0]
        self.assertEqual(item['symbol'], '005930.KS')
        self.assertGreater(item['gamma_score'], 0)
        self.assertEqual(item['eps_status'], 'strong_growth')

    @patch('sepa.agents.gamma.read_company_snapshot', return_value={'roe': 10.0, 'opm': 8.0})
    @patch('sepa.agents.gamma.MacroDataProvider')
    @patch('sepa.agents.gamma.DartProvider')
    def test_chem_bonus_applied(self, mock_dart_cls, mock_macro_cls, mock_snapshot):
        mock_macro = MagicMock()
        mock_macro.get_snapshot.return_value = {'wti': 75.0}
        mock_macro_cls.return_value = mock_macro

        mock_dart = MagicMock()
        mock_dart.get_growth_hint.return_value = {'growth_hint': 1.0, 'status': 'positive_growth', 'latest_yoy': 0.1, 'acceleration': 0.0}
        mock_dart_cls.return_value = mock_dart

        from sepa.agents.gamma import GammaResearcher
        researcher = GammaResearcher()
        result = researcher.run([{'symbol': '051910.KS', 'confidence': 5.0}])

        item = result['general'][0]
        self.assertGreater(item['chem_bonus'], 0)
        self.assertEqual(len(result['chem']), 1)

    @patch('sepa.agents.gamma.read_company_snapshot', return_value=None)
    @patch('sepa.agents.gamma.MacroDataProvider')
    @patch('sepa.agents.gamma.DartProvider')
    def test_historical_date_returns_neutral_macro(self, mock_dart_cls, mock_macro_cls, mock_snapshot):
        mock_macro = MagicMock()
        mock_macro_cls.return_value = mock_macro

        mock_dart = MagicMock()
        mock_dart.get_growth_hint.return_value = {'growth_hint': 0.5, 'status': 'weak', 'latest_yoy': -0.1, 'acceleration': 0.0}
        mock_dart_cls.return_value = mock_dart

        from sepa.agents.gamma import GammaResearcher
        researcher = GammaResearcher()
        result = researcher.run([{'symbol': '005930.KS', 'confidence': 3.0}], as_of_date='20240101')

        self.assertEqual(result['macro_snapshot']['source'], 'historical-neutral')
        mock_macro.get_snapshot.assert_not_called()


if __name__ == '__main__':
    unittest.main()
