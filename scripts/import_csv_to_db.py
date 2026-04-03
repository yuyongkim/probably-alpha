"""One-time import: 2716 OHLCV CSV files → SQLite ohlcv.db.

Usage:
    python scripts/import_csv_to_db.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sepa.data.ohlcv_db import ensure_db, import_csv_dir, get_all_symbols, DB_PATH

CSV_DIR = ROOT / '.omx' / 'artifacts' / 'market-data' / 'ohlcv'


def main() -> None:
    print(f'Source: {CSV_DIR}')
    print(f'Target: {DB_PATH}')
    csv_count = len(list(CSV_DIR.glob('*.csv')))
    print(f'CSV files: {csv_count}')

    start = time.time()
    ensure_db()
    total = import_csv_dir(CSV_DIR, verbose=True)
    elapsed = time.time() - start

    symbols = get_all_symbols()
    db_size_mb = DB_PATH.stat().st_size / (1024 * 1024)

    print(f'\nDone in {elapsed:.1f}s')
    print(f'  Rows imported: {total:,}')
    print(f'  Symbols: {len(symbols)}')
    print(f'  DB size: {db_size_mb:.1f} MB')


if __name__ == '__main__':
    main()
