from __future__ import annotations

import unittest

from sepa.analysis.patterns import detect_support_resistance


class SupportResistanceTest(unittest.TestCase):
    def test_detect_support_and_resistance_levels(self) -> None:
        closes = [
            105, 104, 103, 102, 101, 100, 101, 103, 106, 110,
            114, 118, 120, 119, 117, 115, 112, 109, 106, 103,
            100, 102, 105, 109, 113, 117, 120, 118, 116, 114,
            112, 109, 106, 104, 102, 101, 103, 106, 110, 112,
            115,
        ]
        price_series = [
            {
                'date': f'2026-01-{idx + 1:02d}',
                'close': close,
            }
            for idx, close in enumerate(closes)
        ]

        result = detect_support_resistance(price_series, order=2, tolerance_pct=2.0, lookback=60)

        self.assertAlmostEqual(result['current_price'], 115.0, delta=0.1)
        self.assertIsNotNone(result['nearest_support'])
        self.assertIsNotNone(result['nearest_resistance'])
        self.assertAlmostEqual(result['nearest_support']['price'], 100.5, delta=3.0)
        self.assertAlmostEqual(result['nearest_resistance']['price'], 120.0, delta=3.0)


if __name__ == '__main__':
    unittest.main()
