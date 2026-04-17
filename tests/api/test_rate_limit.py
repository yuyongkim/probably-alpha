from __future__ import annotations

import unittest

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from sepa.api.rate_limit import (
    RateLimitMiddleware,
    RateLimitPolicy,
    resolve_client_ip,
)


class ProxyAwareClientIpTest(unittest.TestCase):
    def test_uses_proxy_headers_only_when_trusted(self) -> None:
        app = FastAPI()

        @app.get('/whoami')
        def whoami(request: Request) -> dict:
            trusted = RateLimitPolicy(trust_proxy_headers=True, trusted_proxy_ips=('testclient',))
            untrusted = RateLimitPolicy(trust_proxy_headers=True, trusted_proxy_ips=('10.0.0.1',))
            return {
                'trusted': resolve_client_ip(request, trusted),
                'untrusted': resolve_client_ip(request, untrusted),
            }

        client = TestClient(app)
        response = client.get('/whoami', headers={'X-Forwarded-For': '198.51.100.10, 10.0.0.5', 'X-Real-IP': '198.51.100.11'})
        body = response.json()

        self.assertEqual(body['trusted'], '198.51.100.10')
        self.assertEqual(body['untrusted'], 'testclient')


class RateLimitMiddlewareIntegrationTest(unittest.TestCase):
    def test_sets_headers_and_honors_proxy_when_enabled(self) -> None:
        app = FastAPI()
        app.add_middleware(
            RateLimitMiddleware,
            policy=RateLimitPolicy(
                api_rpm=1,
                static_rpm=2,
                trust_proxy_headers=True,
                trusted_proxy_ips=('testclient',),
            ),
        )

        @app.get('/api/ping')
        def ping() -> dict:
            return {'ok': True}

        client = TestClient(app)
        headers = {'X-Forwarded-For': '203.0.113.9'}

        first = client.get('/api/ping', headers=headers)
        second = client.get('/api/ping', headers=headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.headers['x-ratelimit-limit'], '1')
        self.assertEqual(first.headers['x-ratelimit-remaining'], '0')
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.headers['x-ratelimit-limit'], '1')
        self.assertEqual(second.headers['x-ratelimit-remaining'], '0')
        self.assertIn('retry-after', second.headers)


if __name__ == '__main__':
    unittest.main()
