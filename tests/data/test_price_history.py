from __future__ import annotations

import unittest

from sepa.data.price_history import normalize_date_token, is_business_date_token


class NormalizeDateTokenTest(unittest.TestCase):
    def test_yyyymmdd_passthrough(self):
        self.assertEqual(normalize_date_token('20260313'), '20260313')

    def test_dashed_format(self):
        self.assertEqual(normalize_date_token('2026-03-13'), '20260313')

    def test_none_returns_empty(self):
        self.assertEqual(normalize_date_token(None), '')

    def test_empty_returns_empty(self):
        self.assertEqual(normalize_date_token(''), '')

    def test_non_date_string_stripped(self):
        result = normalize_date_token('not-a-date')
        self.assertEqual(result, 'notadate')

    def test_falsy_value_is_empty(self):
        self.assertFalse(normalize_date_token(None))
        self.assertFalse(normalize_date_token(''))


class IsBusinessDateTokenTest(unittest.TestCase):
    def test_weekday(self):
        self.assertTrue(is_business_date_token('20260313'))

    def test_saturday(self):
        self.assertFalse(is_business_date_token('20260314'))

    def test_sunday(self):
        self.assertFalse(is_business_date_token('20260315'))

    def test_invalid_token(self):
        self.assertFalse(is_business_date_token('invalid'))


if __name__ == '__main__':
    unittest.main()
