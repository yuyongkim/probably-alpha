from __future__ import annotations

import unittest
from unittest.mock import patch


class DeltaRiskManagerTest(unittest.TestCase):
    @patch('sepa.agents.delta.ExecutionPlanner')
    def test_run_builds_plans_for_top3(self, mock_planner_cls):
        mock_planner = mock_planner_cls.return_value
        mock_planner.build_plan.return_value = {
            'symbol': '005930.KS',
            'name': '삼성전자',
            'entry': 70000,
            'stop': 64750,
            'target': 80500,
            'qty': 38,
            'rr_ratio': 2.0,
        }

        from sepa.agents.delta import DeltaRiskManager
        delta = DeltaRiskManager()
        gamma_payload = {
            'general': [
                {'symbol': '005930.KS', 'gamma_score': 8.0},
                {'symbol': '000660.KS', 'gamma_score': 7.0},
                {'symbol': '051910.KS', 'gamma_score': 6.0},
                {'symbol': '035420.KS', 'gamma_score': 5.0},
            ],
        }
        plans = delta.run(gamma_payload)

        self.assertEqual(len(plans), 3)
        self.assertEqual(mock_planner.build_plan.call_count, 3)

    @patch('sepa.agents.delta.ExecutionPlanner')
    def test_run_skips_null_entry(self, mock_planner_cls):
        mock_planner = mock_planner_cls.return_value
        mock_planner.build_plan.return_value = {
            'entry': None, 'stop': None, 'target': None, 'qty': None, 'rr_ratio': None,
        }

        from sepa.agents.delta import DeltaRiskManager
        delta = DeltaRiskManager()
        plans = delta.run({'general': [{'symbol': 'X', 'gamma_score': 1.0}]})
        self.assertEqual(len(plans), 0)


if __name__ == '__main__':
    unittest.main()
