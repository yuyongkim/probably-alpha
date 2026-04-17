from __future__ import annotations

from pathlib import Path
import re
import unittest

from fastapi.testclient import TestClient

from config.settings import Settings
from sepa.api.csp import build_content_security_policy
from sepa.api.factory import build_cors_middleware_options, create_app


class BuildCorsMiddlewareOptionsTest(unittest.TestCase):
    def test_default_dev_origins_are_preserved(self) -> None:
        current_settings = Settings(
            cors_origins=('http://127.0.0.1:8080', 'http://localhost:8080'),
            cors_allow_credentials=False,
        )

        options = build_cors_middleware_options(current_settings)

        self.assertEqual(
            options['allow_origins'],
            ['http://127.0.0.1:8080', 'http://localhost:8080'],
        )
        self.assertFalse(options['allow_credentials'])
        self.assertIn('X-SEPA-Admin-Token', options['allow_headers'])

    def test_wildcard_origin_forces_credentials_off(self) -> None:
        current_settings = Settings(
            cors_origins=('*',),
            cors_allow_credentials=True,
        )

        options = build_cors_middleware_options(current_settings)

        self.assertEqual(
            options['allow_origins'],
            [
                'https://sepa.yule.pics',
                'http://localhost:8200',
                'http://127.0.0.1:8200',
                'http://localhost:8280',
                'http://127.0.0.1:8280',
            ],
        )
        self.assertFalse(options['allow_credentials'])


class SecurityHeadersMiddlewareTest(unittest.TestCase):
    def test_csp_disables_unsafe_inline_for_scripts(self) -> None:
        app = create_app(Settings(enable_docs=False))
        client = TestClient(app)

        response = client.get('/market-wizards-korea.html')

        self.assertEqual(response.status_code, 200)
        csp = response.headers['content-security-policy']
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)
        self.assertNotIn('sha256-', csp)
        self.assertIn("style-src 'self' 'unsafe-inline' https://fonts.googleapis.com", csp)
        self.assertIn("font-src 'self' https://fonts.gstatic.com", csp)
        self.assertIn("object-src 'none'", csp)

    def test_target_pages_no_longer_embed_inline_scripts(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        inline_script_pattern = re.compile(r'<script(?![^>]*\bsrc=)[^>]*>', re.IGNORECASE)
        html_files = [
            repo_root / 'sepa' / 'frontend' / 'backtest.html',
            repo_root / 'sepa' / 'frontend' / 'etf-mobile.html',
            repo_root / 'sepa' / 'frontend' / 'glossary.html',
            repo_root / 'sepa' / 'frontend' / 'index.html',
            repo_root / 'sepa' / 'frontend' / 'kis-mobile.html',
            repo_root / 'sepa' / 'frontend' / 'market-wizards-korea.html',
            repo_root / 'sepa' / 'frontend' / 'market-wizards-people.html',
            repo_root / 'sepa' / 'frontend' / 'market-wizards.html',
            repo_root / 'sepa' / 'frontend' / 'overseas-mobile.html',
            repo_root / 'sepa' / 'frontend' / 'strategy-follow.html',
            repo_root / 'sepa' / 'frontend' / 'trader-debate.html',
            repo_root / 'sepa' / 'frontend' / 'wizard-screener.html',
        ]

        for html_file in html_files:
            with self.subTest(html_file=html_file.name):
                source = html_file.read_text(encoding='utf-8')
                self.assertIsNone(inline_script_pattern.search(source))

    def test_csp_builder_no_longer_requires_script_hashes(self) -> None:
        frontend_dir = Path(__file__).resolve().parents[2] / 'sepa' / 'frontend'
        csp = build_content_security_policy(frontend_dir)

        self.assertIn("script-src 'self'", csp)
        self.assertNotIn('sha256-', csp)


class DocsExposureTest(unittest.TestCase):
    def test_docs_disabled_by_default(self) -> None:
        app = create_app(Settings(enable_docs=False))
        client = TestClient(app)

        response = client.get('/docs')

        self.assertEqual(response.status_code, 404)

    def test_docs_can_be_enabled_explicitly(self) -> None:
        app = create_app(Settings(enable_docs=True))
        client = TestClient(app)

        response = client.get('/docs')

        self.assertEqual(response.status_code, 200)


class RateLimitMiddlewareTest(unittest.TestCase):
    def test_rate_limit_headers_are_exposed_on_success(self) -> None:
        app = create_app(Settings(rate_limit_api_rpm=2, rate_limit_static_rpm=1, rate_limit_window_seconds=60))
        client = TestClient(app)

        response = client.get('/api/health')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['x-ratelimit-limit'], '2')
        self.assertEqual(response.headers['x-ratelimit-remaining'], '1')
        self.assertEqual(response.headers['x-ratelimit-reset'], '60')

    def test_rate_limit_uses_trusted_proxy_headers_when_enabled(self) -> None:
        app = create_app(
            Settings(
                rate_limit_api_rpm=1,
                rate_limit_static_rpm=1,
                rate_limit_window_seconds=60,
                rate_limit_trust_proxy_headers=True,
                rate_limit_trusted_proxy_ips=('testclient',),
            )
        )
        client = TestClient(app)

        first = client.get('/api/health', headers={'X-Forwarded-For': '198.51.100.10'})
        second = client.get('/api/health', headers={'X-Forwarded-For': '203.0.113.20'})
        third = client.get('/api/health', headers={'X-Forwarded-For': '198.51.100.10'})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)
        self.assertEqual(third.headers['retry-after'], '60')


if __name__ == '__main__':
    unittest.main()
