from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from sepa.data.ohlcv_db import ensure_db, read_ohlcv, upsert_rows


class OhlcvDbOptionalColumnsTest(unittest.TestCase):
    def test_upsert_and_read_preserves_open_high_low(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'ohlcv.db'
            ensure_db(db_path)
            upsert_rows(
                '069500',
                [
                    {
                        'date': '2026-04-15',
                        'open': 94000,
                        'high': 95000,
                        'low': 93500,
                        'close': 94500,
                        'volume': 123456,
                    }
                ],
                db_path=db_path,
            )

            rows = read_ohlcv('069500', db_path=db_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['open'], 94000.0)
        self.assertEqual(rows[0]['high'], 95000.0)
        self.assertEqual(rows[0]['low'], 93500.0)
        self.assertEqual(rows[0]['close'], 94500.0)


if __name__ == '__main__':
    unittest.main()
