from __future__ import annotations

import unittest

from sepa.api.services_kis_catalog import kis_product_catalog_payload


class KisCatalogServiceTest(unittest.TestCase):
    def test_catalog_contains_domestic_etf_family(self) -> None:
        payload = kis_product_catalog_payload()
        family_ids = {item['family_id'] for item in payload['items']}

        self.assertIn('domestic_etf_etn', family_ids)
        self.assertIn('domestic_stock', family_ids)

    def test_catalog_filters_backtestable_families(self) -> None:
        payload = kis_product_catalog_payload(backtestable_only=True)
        family_ids = {item['family_id'] for item in payload['items']}

        self.assertIn('domestic_stock', family_ids)
        self.assertIn('domestic_etf_etn', family_ids)
        self.assertNotIn('domestic_bond', family_ids)
        self.assertNotIn('domestic_futureoption', family_ids)

    def test_catalog_filters_orderable_families(self) -> None:
        payload = kis_product_catalog_payload(orderable_only=True)
        family_ids = {item['family_id'] for item in payload['items']}

        self.assertIn('domestic_stock', family_ids)
        self.assertIn('domestic_etf_etn', family_ids)
        self.assertIn('overseas_stock', family_ids)
        self.assertNotIn('elw', family_ids)


if __name__ == '__main__':
    unittest.main()
