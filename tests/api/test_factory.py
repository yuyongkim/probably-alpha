from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from config.settings import Settings
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
    def test_csp_allows_google_font_assets_used_by_frontend(self) -> None:
        app = create_app()
        client = TestClient(app)

        response = client.get('/market-wizards-korea.html')

        self.assertEqual(response.status_code, 200)
        csp = response.headers['content-security-policy']
        self.assertIn("style-src 'self' 'unsafe-inline' https://fonts.googleapis.com", csp)
        self.assertIn("font-src 'self' https://fonts.gstatic.com", csp)


if __name__ == '__main__':
    unittest.main()
