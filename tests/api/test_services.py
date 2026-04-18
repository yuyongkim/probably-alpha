from __future__ import annotations

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from sepa.api import services
from sepa.api.services_dashboard import _latest_complete_dashboard_dir


class ApiServicesTest(unittest.TestCase):
    def test_resolve_dir_missing_bundle_is_read_only(self) -> None:
        with (
            patch.object(services, 'SIGNALS_ROOT', Path('data/nonexistent-test-signals')),
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

    def test_dashboard_falls_back_to_latest_complete_signal_bundle(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            latest = root / '20260417'
            previous = root / '20260414'
            latest.mkdir(parents=True, exist_ok=True)
            previous.mkdir(parents=True, exist_ok=True)

            required = [
                'alpha-passed.json',
                'beta-vcp-candidates.json',
                'delta-risk-plan.json',
                'omega-final-picks.json',
                'leader-stocks.json',
                'leader-sectors.json',
                'recommendations.json',
            ]
            for name in required:
                (previous / name).write_text('[]', encoding='utf-8')
            # leave latest incomplete on purpose
            (latest / 'alpha-passed.json').write_text('[]', encoding='utf-8')

            resolved = _latest_complete_dashboard_dir(latest)

            self.assertEqual(resolved, previous)

    def test_dashboard_raises_when_no_complete_bundle_exists(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            latest = root / '20260417'
            latest.mkdir(parents=True, exist_ok=True)
            (latest / 'alpha-passed.json').write_text('[]', encoding='utf-8')

            with self.assertRaises(HTTPException) as ctx:
                _latest_complete_dashboard_dir(latest)

            self.assertEqual(ctx.exception.status_code, 404)
            self.assertIn('missing file', ctx.exception.detail)


if __name__ == '__main__':
    unittest.main()
