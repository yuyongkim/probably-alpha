"""Update KRX universe CSV from ohlcv.db symbol_meta.

Generates config/krx_universe.csv with all actively traded symbols.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sepa.data.ohlcv_db import get_active_universe


def main() -> None:
    out_path = ROOT / 'config' / 'krx_universe.csv'

    universe = get_active_universe(min_date='20260301', min_rows=200)
    print(f'Active symbols: {len(universe)}')

    with out_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'name', 'sector', 'industry'])
        writer.writeheader()
        for r in universe:
            writer.writerow({
                'symbol': r.get('symbol', ''),
                'name': r.get('name', ''),
                'sector': r.get('sector', ''),
                'industry': r.get('industry', ''),
            })

    print(f'Written: {out_path} ({len(universe)} rows)')


if __name__ == '__main__':
    main()
