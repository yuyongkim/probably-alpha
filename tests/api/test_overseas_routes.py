from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from config.settings import Settings
from sepa.api.factory import create_app
from sepa.api.services_overseas import _call_with_retry
from sepa.brokers import KisApiError


class OverseasStockRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(Settings(enable_docs=False)))

    def test_overseas_stock_analysis_route_returns_payload(self) -> None:
        with patch(
            'sepa.api.routes_public.overseas_stock_analysis_payload',
            return_value={'symbol': 'AAPL', 'name': 'APPLE INC', 'exchange_code': 'NAS'},
        ) as mocked:
            response = self.client.get('/api/overseas/stock/AAPL/analysis?exchange_code=NAS&product_type_code=512')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['symbol'], 'AAPL')
        mocked.assert_called_once()


class OverseasRetryTest(unittest.TestCase):
    def test_call_with_retry_recovers_from_rate_limit(self) -> None:
        state = {'calls': 0}

        def flaky():
            state['calls'] += 1
            if state['calls'] == 1:
                raise KisApiError(500, '초당 거래건수를 초과하였습니다.')
            return {'ok': True}

        with patch('time.sleep', return_value=None):
            payload = _call_with_retry(flaky)

        self.assertEqual(state['calls'], 2)
        self.assertTrue(payload['ok'])


if __name__ == '__main__':
    unittest.main()
