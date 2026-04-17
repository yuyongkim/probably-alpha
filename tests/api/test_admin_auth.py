from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from config.settings import Settings
from sepa.api.factory import create_app


class AdminAuthHardeningTest(unittest.TestCase):
    def _response_for(self, headers: dict[str, str] | None = None):
        client = TestClient(create_app(Settings(enable_docs=False)))
        with patch('sepa.api.routes_admin.run_backtest_job', return_value={'ok': True}):
            return client.post('/api/admin/backtest/run', headers=headers or {})

    def test_missing_admin_token_configuration_returns_503(self) -> None:
        with patch.dict(
            os.environ,
            {'SEPA_ADMIN_TOKEN': '', 'SEPA_ADMIN_TOKENS': '', 'SEPA_ADMIN_PREVIOUS_TOKENS': ''},
            clear=False,
        ):
            response = self._response_for(headers={'Authorization': 'Bearer anything'})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()['detail'],
            'admin authentication unavailable',
        )
        self.assertEqual(response.headers['www-authenticate'], 'Bearer realm="sepa-admin"')

    def test_primary_bearer_token_is_accepted(self) -> None:
        with patch.dict(
            os.environ,
            {'SEPA_ADMIN_TOKEN': 'current-secret', 'SEPA_ADMIN_TOKENS': '', 'SEPA_ADMIN_PREVIOUS_TOKENS': ''},
            clear=False,
        ):
            response = self._response_for(headers={'Authorization': 'Bearer current-secret'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ok'], True)

    def test_previous_rotation_token_is_accepted(self) -> None:
        with patch.dict(
            os.environ,
            {'SEPA_ADMIN_TOKEN': 'current-secret', 'SEPA_ADMIN_PREVIOUS_TOKENS': 'older-secret', 'SEPA_ADMIN_TOKENS': ''},
            clear=False,
        ):
            response = self._response_for(headers={'Authorization': 'Bearer older-secret'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ok'], True)

    def test_legacy_header_can_be_disabled(self) -> None:
        with patch.dict(
            os.environ,
            {
                'SEPA_ADMIN_TOKEN': 'current-secret',
                'SEPA_ADMIN_TOKENS': '',
                'SEPA_ADMIN_PREVIOUS_TOKENS': '',
                'SEPA_ADMIN_ALLOW_LEGACY_HEADER': '0',
            },
            clear=False,
        ):
            response = self._response_for(headers={'X-SEPA-Admin-Token': 'current-secret'})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['detail'], 'admin authentication failed')
        self.assertEqual(response.headers['www-authenticate'], 'Bearer realm="sepa-admin"')

    def test_legacy_header_can_be_used_for_rotation_window(self) -> None:
        with patch.dict(
            os.environ,
            {
                'SEPA_ADMIN_TOKEN': 'current-secret',
                'SEPA_ADMIN_TOKENS': '',
                'SEPA_ADMIN_PREVIOUS_TOKENS': '',
                'SEPA_ADMIN_ALLOW_LEGACY_HEADER': '1',
            },
            clear=False,
        ):
            response = self._response_for(headers={'X-SEPA-Admin-Token': 'current-secret'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['ok'], True)

    def test_malformed_authorization_header_is_rejected_generically(self) -> None:
        with patch.dict(
            os.environ,
            {'SEPA_ADMIN_TOKEN': 'current-secret', 'SEPA_ADMIN_TOKENS': '', 'SEPA_ADMIN_PREVIOUS_TOKENS': ''},
            clear=False,
        ):
            response = self._response_for(headers={'Authorization': 'Token current-secret'})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['detail'], 'admin authentication failed')
        self.assertEqual(response.headers['www-authenticate'], 'Bearer realm="sepa-admin"')


if __name__ == '__main__':
    unittest.main()
