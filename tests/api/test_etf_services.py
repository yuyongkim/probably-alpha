from __future__ import annotations

import unittest
from unittest.mock import patch

from sepa.api.services_etf import _fetch_etf_history_windows, run_etf_backtest_payload
from sepa.brokers import KisApiError


class EtfHistoryWindowFetchTest(unittest.TestCase):
    def test_rate_limit_retry_then_success(self) -> None:
        class FakeBroker:
            def __init__(self) -> None:
                self.calls = 0

            def daily_chart(self, symbol: str, *, date_from: str, date_to: str) -> dict:
                self.calls += 1
                if self.calls == 1:
                    raise KisApiError(500, '초당 거래건수를 초과하였습니다.')
                return {
                    'rows': [
                        {'date': '2026-04-15', 'open': 100, 'high': 110, 'low': 95, 'close': 105, 'volume': 1000},
                        {'date': '2026-04-16', 'open': 106, 'high': 111, 'low': 101, 'close': 108, 'volume': 1200},
                    ]
                }

        broker = FakeBroker()
        with patch('time.sleep', return_value=None):
            rows = _fetch_etf_history_windows(
                broker,
                '069500',
                date_from='20260415',
                date_to='20260416',
                max_windows=1,
            )

        self.assertEqual(broker.calls, 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]['close'], 108)


class EtfBacktestPayloadTest(unittest.TestCase):
    def test_run_etf_backtest_payload_reports_missing_symbols(self) -> None:
        fake_result = {
            'strategy': 'ETF Custom',
            'metrics': {'total_return': 0.1},
            'trades': [],
        }

        class FakeEngine:
            def __init__(self, strategy) -> None:
                self.strategy = strategy

            def run(self, start: str, end: str) -> dict:
                return dict(fake_result)

        with (
            patch('sepa.api.services_etf.read_ohlcv_batch', return_value={'069500': {'closes': [1] * 250, 'volumes': [1] * 250}}),
            patch('sepa.api.services_etf.BacktestEngine', FakeEngine),
        ):
            result = run_etf_backtest_payload(
                ['069500', '360750'],
                start='20250102',
                end='20250401',
            )

        self.assertEqual(result['available_symbols'], ['069500'])
        self.assertEqual(result['missing_symbols'], ['360750'])


if __name__ == '__main__':
    unittest.main()
