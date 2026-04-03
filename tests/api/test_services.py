from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from sepa.api import services


class ApiServicesTest(unittest.TestCase):
    def test_resolve_dir_missing_bundle_is_read_only(self) -> None:
        with (
            patch.object(services, 'SIGNALS_ROOT', Path('.omx/nonexistent-test-signals')),
            patch.object(services, 'available_dates', return_value=['20250103']),
            patch.object(services, 'nearest_available_date', return_value='20250103'),
            patch.object(services, 'build_after_close') as build_after_close,
        ):
            with self.assertRaises(HTTPException) as ctx:
                services.resolve_dir('2025-01-03')

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn('POST /api/admin/daily-signals', ctx.exception.detail)
        build_after_close.assert_not_called()

    def test_build_daily_signals_calls_after_close_explicitly(self) -> None:
        with patch.object(services, 'build_after_close', return_value='20250103') as build_after_close:
            payload = services.build_daily_signals('2025-01-03', refresh_live=True)

        build_after_close.assert_called_once_with(as_of_date='20250103', refresh_live=True)
        self.assertEqual(
            payload,
            {
                'status': 'ok',
                'date_dir': '20250103',
                'refresh_live': True,
            },
        )

    def test_backfill_history_payload_uses_explicit_write_path(self) -> None:
        with (
            patch.object(services, 'nearest_available_date', return_value='20250103'),
            patch.object(services, 'trailing_available_dates', return_value=['20241227', '20250103']),
            patch.object(services, 'leading_available_dates', return_value=['20250103', '20250110']),
            patch.object(services, 'backfill_history') as backfill_history,
        ):
            payload = services.backfill_history_payload(
                date_to='2025-01-03',
                lookback_days=10,
                forward_days=5,
                force=True,
            )

        backfill_history.assert_called_once_with(
            days=None,
            date_from='20241227',
            date_to='20250110',
            force=True,
        )
        self.assertEqual(
            payload,
            {
                'status': 'ok',
                'resolved_date': '20250103',
                'date_from': '20241227',
                'date_to': '20250110',
                'force': True,
            },
        )


if __name__ == '__main__':
    unittest.main()
