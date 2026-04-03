from __future__ import annotations

import unittest

from config.settings import Settings
from sepa.api.factory import build_cors_middleware_options


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

        self.assertEqual(options['allow_origins'], ['*'])
        self.assertFalse(options['allow_credentials'])


if __name__ == '__main__':
    unittest.main()
