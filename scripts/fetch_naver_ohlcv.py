"""Fetch full OHLCV (open/high/low/close/volume) from Naver fchart API.

fchart.stock.naver.com provides 1000+ days of OHLCV data per symbol,
no authentication required. This fills the open/high/low columns
in ohlcv.db that were previously missing.

Usage:
    python scripts/fetch_naver_ohlcv.py              # all stocks
    python scripts/fetch_naver_ohlcv.py --limit 50   # test
    python scripts/fetch_naver_ohlcv.py --days 250   # last 1 year only
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / 'data' / 'ohlcv.db'
FCHART_URL = 'https://fchart.stock.naver.com/sise.nhn'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def fetch_ohlcv(symbol: str, count: int = 1000) -> list[dict]:
    """Fetch OHLCV from Naver fchart. Returns [{date, open, high, low, close, volume}]."""
    url = f'{FCHART_URL}?symbol={symbol}&timeframe=day&count={count}&requestType=0'
    try:
        raw = urlopen(Request(url, headers=HEADERS), timeout=15).read()
        text = raw.decode('euc-kr', errors='replace').replace('encoding="euc-kr"', '')
        root = ET.fromstring(text)
    except Exception:
        return []

    rows = []
    for item in root.findall('.//item'):
        parts = item.get('data', '').split('|')
        if len(parts) < 6:
            continue
        try:
            rows.append({
                'date': parts[0],
                'open': float(parts[1]),
                'high': float(parts[2]),
                'low': float(parts[3]),
                'close': float(parts[4]),
                'volume': int(float(parts[5])),
            })
        except (ValueError, IndexError):
            continue
    return rows


def process_one(symbol: str, count: int) -> tuple[str, int]:
    """Fetch and save one symbol. Returns (symbol, rows_saved)."""
    rows = fetch_ohlcv(symbol, count)
    if not rows:
        return symbol, 0

    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute('PRAGMA journal_mode=DELETE')
    conn.execute('PRAGMA busy_timeout=30000')

    conn.executemany(
        '''INSERT OR REPLACE INTO ohlcv (symbol, trade_date, open, high, low, close, volume)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        [(symbol, r['date'], r['open'], r['high'], r['low'], r['close'], r['volume']) for r in rows],
    )
    conn.commit()
    conn.close()
    return symbol, len(rows)


def main():
    parser = argparse.ArgumentParser(description='Fetch OHLCV from Naver fchart')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--days', type=int, default=1000, help='Number of trading days to fetch')
    parser.add_argument('--workers', type=int, default=10, help='Parallel workers (fchart has no rate limit)')
    args = parser.parse_args()

    # Get symbol list from meta.db
    meta_db = PROJECT_ROOT / 'data' / 'meta.db'
    conn = sqlite3.connect(str(meta_db))
    all_symbols = [r[0] for r in conn.execute('SELECT symbol FROM symbol_meta ORDER BY symbol').fetchall()]
    conn.close()

    todo = all_symbols[args.skip:]
    if args.limit > 0:
        todo = todo[:args.limit]

    print(f'Target: {len(todo)} symbols, {args.days} days, {args.workers} workers', flush=True)

    ok = 0
    err = 0
    total_rows = 0
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_one, sym, args.days): sym for sym in todo}

        for f in as_completed(futures):
            try:
                symbol, n = f.result()
                if n > 0:
                    ok += 1
                    total_rows += n
                else:
                    err += 1
            except Exception:
                err += 1

            done = ok + err
            if done % 100 == 0:
                elapsed = time.time() - t0
                rate = done / elapsed if elapsed > 0 else 1
                remain = (len(todo) - done) / rate
                print(f'  [{done}/{len(todo)}] ok={ok} err={err} rows={total_rows:,} {elapsed:.0f}s ~{remain:.0f}s', flush=True)

    elapsed = time.time() - t0
    print(f'\nDONE {elapsed:.0f}s: ok={ok} err={err} total_rows={total_rows:,}', flush=True)


if __name__ == '__main__':
    main()
