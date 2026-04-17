from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from config.settings import Settings
from sepa.api.factory import create_app


class KisPublicRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(Settings(enable_docs=False)))

    def test_kis_health_route_returns_payload(self) -> None:
        with patch(
            'sepa.api.routes_public.kis_health_payload',
            return_value={'auth_ok': True, 'env': 'prod'},
        ):
            response = self.client.get('/api/kis/health')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['auth_ok'])

    def test_kis_catalog_route_returns_payload(self) -> None:
        with patch(
            'sepa.api.routes_public.kis_product_catalog_payload',
            return_value={'count': 2, 'items': [{'family_id': 'domestic_stock'}, {'family_id': 'domestic_etf_etn'}]},
        ) as mocked:
            response = self.client.get('/api/kis/catalog')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 2)
        mocked.assert_called_once()

    def test_etf_analysis_route_returns_payload(self) -> None:
        with patch(
            'sepa.api.routes_public.etf_analysis_payload',
            return_value={'symbol': '069500', 'name': 'KODEX 200'},
        ) as mocked:
            response = self.client.get('/api/etf/069500/analysis')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['symbol'], '069500')
        mocked.assert_called_once()

    def test_etf_profile_recommendations_route_returns_payload(self) -> None:
        with patch(
            'sepa.api.routes_public.etf_profile_recommendations_payload',
            return_value={'risk_profile': 'balanced', 'count': 1, 'items': [{'symbol': '069500', 'score': 88.5}]},
        ):
            response = self.client.post(
                '/api/etf/recommendations/profile',
                json={'symbols': ['069500'], 'risk_profile': 'balanced'},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)


class KisAdminRoutesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(Settings(enable_docs=False)))

    def test_kis_order_preview_requires_admin_token(self) -> None:
        with patch.dict(os.environ, {'SEPA_ADMIN_TOKEN': ''}):
            response = self.client.post('/api/admin/kis/order-preview', json={'symbol': '069500', 'order_price': 100000})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['detail'], 'admin authentication unavailable')

    def test_kis_order_preview_route_returns_payload(self) -> None:
        with patch.dict(os.environ, {'SEPA_ADMIN_TOKEN': 'topsecret'}):
            with patch(
                'sepa.api.routes_admin.kis_order_preview_payload',
                return_value={'symbol': '069500', 'preview': {'max_buy_qty': 10}},
            ) as mocked:
                response = self.client.post(
                    '/api/admin/kis/order-preview',
                    json={'symbol': '069500', 'order_price': 100000},
                    headers={'Authorization': 'Bearer topsecret'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['preview']['max_buy_qty'], 10)
        mocked.assert_called_once()

    def test_kis_order_cash_route_returns_payload(self) -> None:
        with patch.dict(os.environ, {'SEPA_ADMIN_TOKEN': 'topsecret'}):
            with patch(
                'sepa.api.routes_admin.kis_order_cash_payload',
                return_value={'symbol': '069500', 'order': {'order_no': '12345'}},
            ) as mocked:
                response = self.client.post(
                    '/api/admin/kis/order-cash',
                    json={'side': 'buy', 'symbol': '069500', 'quantity': 1, 'order_price': 100000},
                    headers={'Authorization': 'Bearer topsecret'},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['order']['order_no'], '12345')
        mocked.assert_called_once()


if __name__ == '__main__':
    unittest.main()
