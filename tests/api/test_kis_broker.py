from __future__ import annotations

import unittest
from unittest.mock import patch

from sepa.brokers.kis import KisBroker, KisConfig, _TOKEN_CACHE


class KisBrokerTokenCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        _TOKEN_CACHE.clear()

    def test_issue_token_cache_is_shared_across_instances(self) -> None:
        config = KisConfig(
            app_key='app',
            app_secret='secret',
            account_no='',
            account_product_code='',
            env='prod',
            base_url='https://example.com',
            order_enabled=False,
        )

        with patch.object(
            KisBroker,
            '_request_json',
            return_value={
                'access_token': 'cached-token',
                'expires_in': 3600,
                'access_token_token_expired': '2026-04-17 23:59:59',
            },
        ) as mocked:
            first = KisBroker(config)
            second = KisBroker(config)

            payload_one = first.issue_token()
            payload_two = second.issue_token()

        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(payload_one['access_token'], 'cached-token')
        self.assertEqual(payload_two['access_token'], 'cached-token')


if __name__ == '__main__':
    unittest.main()
