from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from config.settings import Settings
from sepa.api.factory import create_app
from sepa.api.routes_public import preset_picks
from sepa.backtest.presets import get_preset


class PublicRouteSecurityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(Settings(enable_docs=False)))

    def test_stock_quant_rejects_invalid_symbol(self) -> None:
        response = self.client.get('/api/stock/bad-symbol!/quant')

        self.assertEqual(response.status_code, 400)
        self.assertIn('invalid symbol format', response.json()['detail'])

    def test_backtest_run_is_not_public_get(self) -> None:
        response = self.client.get('/api/backtest/run')

        self.assertEqual(response.status_code, 404)

    def test_backtest_run_requires_admin_token(self) -> None:
        with patch.dict(os.environ, {'SEPA_ADMIN_TOKEN': ''}):
            response = self.client.post('/api/admin/backtest/run')

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['detail'], 'SEPA_ADMIN_TOKEN not configured')

    def test_admin_backtest_run_requires_post_and_returns_results(self) -> None:
        class FakeEngine:
            def __init__(self, strategy) -> None:
                self.strategy = strategy

            def run(self, start: str, end: str) -> dict:
                return {
                    'strategy': self.strategy.name,
                    'period': {'start': start, 'end': end},
                    'metrics': {'total_return': 0.12},
                }

        with patch.dict(os.environ, {'SEPA_ADMIN_TOKEN': 'topsecret'}):
            with patch('sepa.backtest.engine.BacktestEngine', FakeEngine):
                response = self.client.post(
                    '/api/admin/backtest/run?preset=minervini&start=20251112&end=20260402',
                    headers={'Authorization': 'Bearer topsecret'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['strategy'], get_preset('minervini').name)


class PresetCopySafetyTest(unittest.TestCase):
    def test_preset_picks_does_not_mutate_global_preset(self) -> None:
        original_cash = get_preset('minervini').initial_cash

        with patch('sepa.data.ohlcv_db.read_ohlcv_batch', return_value={}):
            payload = preset_picks('minervini', initial_cash=123456789)

        self.assertEqual(payload['error'], 'No price data')
        self.assertEqual(get_preset('minervini').initial_cash, original_cash)


if __name__ == '__main__':
    unittest.main()
