from __future__ import annotations

import unittest
from unittest.mock import patch


class MinerviniRecommenderTest(unittest.TestCase):
    def _make_leader_stock(self, *, symbol='005930.KS', sector_ready=True, alpha=90.0, beta=7.0, gamma=8.0, ret120=0.3):
        return {
            'symbol': symbol,
            'name': '테스트',
            'sector': 'IT',
            'sector_leadership_ready': sector_ready,
            'alpha_score': alpha,
            'beta_confidence': beta,
            'gamma_score': gamma,
            'ret120': ret120,
        }

    @patch('sepa.agents.recommender.build_stock_analysis')
    @patch('sepa.agents.recommender.ExecutionPlanner')
    def test_recommends_strong_stock(self, mock_planner_cls, mock_analysis):
        mock_analysis.return_value = {
            'eps_quality': {'status': 'strong_growth'},
            'least_resistance': {'trend': 'up_least_resistance', 'distance_pct': 0.5},
        }
        mock_planner = mock_planner_cls.return_value
        mock_planner.build_plan.return_value = {
            'entry': 70000, 'stop': 64750, 'target': 80500, 'qty': 38, 'rr_ratio': 2.0,
        }

        from sepa.agents.recommender import MinerviniRecommender
        rec = MinerviniRecommender.__new__(MinerviniRecommender)
        rec.top_n = 3
        rec.planner = mock_planner
        rec.weights = {'alpha': 0.45, 'beta': 0.20, 'gamma': 0.20, 'rs120': 0.10, 'least_resistance': 0.05}
        rec.eps_allowed = {'strong_growth', 'positive_growth'}
        rec.lr_allowed = {'up_least_resistance', 'pullback_in_uptrend'}
        rec.min_score = 40.0

        stocks = [self._make_leader_stock()]
        results = rec.run(stocks, [])
        self.assertEqual(len(results), 1)
        self.assertGreaterEqual(results[0]['recommendation_score'], 40.0)

    @patch('sepa.agents.recommender.build_stock_analysis')
    @patch('sepa.agents.recommender.ExecutionPlanner')
    def test_rejects_weak_eps(self, mock_planner_cls, mock_analysis):
        mock_analysis.return_value = {
            'eps_quality': {'status': 'weak'},
            'least_resistance': {'trend': 'up_least_resistance', 'distance_pct': 0.5},
        }

        from sepa.agents.recommender import MinerviniRecommender
        rec = MinerviniRecommender.__new__(MinerviniRecommender)
        rec.top_n = 3
        rec.planner = mock_planner_cls.return_value
        rec.weights = {'alpha': 0.45, 'beta': 0.20, 'gamma': 0.20, 'rs120': 0.10, 'least_resistance': 0.05}
        rec.eps_allowed = {'strong_growth', 'positive_growth'}
        rec.lr_allowed = {'up_least_resistance', 'pullback_in_uptrend'}
        rec.min_score = 40.0

        stocks = [self._make_leader_stock()]
        results = rec.run(stocks, [])
        self.assertEqual(len(results), 0)

    def test_conviction_levels(self):
        from sepa.agents.recommender import MinerviniRecommender
        self.assertEqual(MinerviniRecommender._conviction(75, 'strong_growth', 'up_least_resistance'), 'A+')
        self.assertEqual(MinerviniRecommender._conviction(65, 'positive_growth', 'up_least_resistance'), 'A')
        self.assertEqual(MinerviniRecommender._conviction(55, 'positive_growth', 'pullback_in_uptrend'), 'B')
        self.assertEqual(MinerviniRecommender._conviction(35, 'weak', 'down'), 'C')


if __name__ == '__main__':
    unittest.main()
