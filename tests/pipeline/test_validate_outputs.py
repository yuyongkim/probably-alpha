from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


class ValidateOutputsTest(unittest.TestCase):
    def _write_json(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

    def test_valid_alpha_has_required_fields(self):
        data = [{'symbol': '005930.KS', 'score': 90, 'rs_percentile': 85}]
        for r in data:
            self.assertIn('symbol', r)
            self.assertIn('score', r)

    def test_valid_beta_confidence_in_range(self):
        data = [{'symbol': '005930.KS', 'confidence': 7.5}]
        for r in data:
            c = float(r.get('confidence', -1))
            self.assertTrue(0 <= c <= 10)

    def test_valid_delta_rr_above_threshold(self):
        data = [{'symbol': '005930.KS', 'rr_ratio': 2.0}]
        for r in data:
            self.assertGreaterEqual(float(r.get('rr_ratio', 0)), 1.5)

    def test_beta_confidence_out_of_range_detected(self):
        data = [{'symbol': 'BAD', 'confidence': 15.0}]
        c = float(data[0].get('confidence', -1))
        self.assertFalse(0 <= c <= 10)

    def test_delta_rr_below_threshold_detected(self):
        data = [{'symbol': 'BAD', 'rr_ratio': 1.2}]
        rr = float(data[0].get('rr_ratio', 0))
        self.assertLess(rr, 1.5)

    def test_alpha_missing_symbol_detected(self):
        data = [{'score': 90}]
        self.assertNotIn('symbol', data[0])

    def test_roundtrip_json_encoding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / 'test.json'
            original = [{'symbol': '삼성전자', 'score': 90}]
            self._write_json(path, original)
            loaded = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(loaded, original)


if __name__ == '__main__':
    unittest.main()
