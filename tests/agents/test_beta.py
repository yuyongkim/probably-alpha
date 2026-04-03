from __future__ import annotations

import unittest

from sepa.agents.beta import BetaChartist, SwingPoint


class BetaChartistTest(unittest.TestCase):
    def test_find_swings_detects_peaks_and_troughs(self):
        closes = [10, 11, 12, 11, 10, 9, 10, 11, 12, 13, 12, 11, 10]
        swings = BetaChartist._find_swings(closes, window=2)
        highs = [s for s in swings if s.kind == 'H']
        lows = [s for s in swings if s.kind == 'L']
        self.assertTrue(len(highs) >= 1)
        self.assertTrue(len(lows) >= 1)

    def test_contractions_positive_only(self):
        swings = [
            SwingPoint(0, 100, 'H'),
            SwingPoint(5, 80, 'L'),
            SwingPoint(10, 95, 'H'),
            SwingPoint(15, 85, 'L'),
        ]
        result = BetaChartist._contractions(swings)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], 0.2, places=2)

    def test_volume_dryup_with_declining_volume(self):
        volumes = [100000] * 40 + [50000] * 20
        ratio = BetaChartist._volume_dryup(volumes)
        self.assertLess(ratio, 1.0)

    def test_volume_dryup_empty(self):
        self.assertEqual(BetaChartist._volume_dryup([]), 1.0)

    def test_confidence_scoring_range(self):
        score = BetaChartist._confidence(waves=3, consistency=0.5, volume_dryup=0.5)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 10.0)

    def test_confidence_perfect_vcp(self):
        score = BetaChartist._confidence(waves=3, consistency=0.5, volume_dryup=0.5)
        self.assertGreater(score, 7.0)

    def test_confidence_poor_vcp(self):
        score = BetaChartist._confidence(waves=7, consistency=1.4, volume_dryup=1.3)
        self.assertLess(score, 3.0)

    def test_fallback_contraction_short_series(self):
        ratio, waves = BetaChartist._fallback_contraction([100.0] * 50)
        self.assertEqual(ratio, 1.0)
        self.assertEqual(waves, 2)

    def test_contraction_consistency_two_contractions(self):
        result = BetaChartist._contraction_consistency([0.2, 0.1])
        self.assertAlmostEqual(result, 0.5, places=2)


if __name__ == '__main__':
    unittest.main()
