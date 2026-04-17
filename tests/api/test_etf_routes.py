from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from config.settings import Settings
from sepa.api.factory import create_app


class EtfUniverseRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(Settings(enable_docs=False)))

    def test_etf_universe_route_returns_payload(self) -> None:
        with patch(
            'sepa.api.routes_public.etf_universe_payload',
            return_value={'count': 1, 'items': [{'symbol': '069500', 'name': 'KODEX 200'}]},
        ) as mocked:
            response = self.client.get('/api/etf/universe')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        mocked.assert_called_once()


class EtfAdminRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(Settings(enable_docs=False)))

    def test_etf_history_backfill_route_requires_admin_token(self) -> None:
        with patch.dict(os.environ, {'SEPA_ADMIN_TOKEN': ''}):
            response = self.client.post('/api/admin/kis/etf-history/backfill', json={'symbols': ['069500']})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['detail'], 'admin authentication unavailable')

    def test_etf_history_backfill_route_returns_payload(self) -> None:
        with patch.dict(os.environ, {'SEPA_ADMIN_TOKEN': 'topsecret'}):
            with patch(
                'sepa.api.routes_admin.backfill_etf_history_payload',
                return_value={'count': 1, 'items': [{'symbol': '069500', 'rows_written': 250}]},
            ) as mocked:
                response = self.client.post(
                    '/api/admin/kis/etf-history/backfill',
                    json={'symbols': ['069500'], 'date_from': '20250101', 'date_to': '20250401'},
                    headers={'Authorization': 'Bearer topsecret'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['items'][0]['rows_written'], 250)
        mocked.assert_called_once()

    def test_etf_backtest_run_route_returns_payload(self) -> None:
        with patch.dict(os.environ, {'SEPA_ADMIN_TOKEN': 'topsecret'}):
            with patch(
                'sepa.api.routes_admin.run_etf_backtest_payload',
                return_value={'strategy': 'ETF Custom', 'available_symbols': ['069500'], 'metrics': {'total_return': 0.2}},
            ) as mocked:
                response = self.client.post(
                    '/api/admin/backtest/etf/run',
                    json={'symbols': ['069500'], 'start': '20250102', 'end': '20250401'},
                    headers={'Authorization': 'Bearer topsecret'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['strategy'], 'ETF Custom')
        mocked.assert_called_once()


if __name__ == '__main__':
    unittest.main()
