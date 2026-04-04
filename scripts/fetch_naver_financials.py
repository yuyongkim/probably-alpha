"""Fetch financial data from Naver Finance for all stocks.

Naver provides clean annual + quarterly financials including consensus estimates.
Rate limit: 1 req/sec (conservative).

Usage:
    python scripts/fetch_naver_financials.py              # all
    python scripts/fetch_naver_financials.py --limit 50   # test
    python scripts/fetch_naver_financials.py --skip 500   # resume
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / 'data' / 'sepa.db'
NAVER_API = 'https://m.stock.naver.com/api/stock'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Naver row title -> our metric key
METRIC_MAP = {
    '매출액': '매출액',
    '영업이익': '영업이익',
    '당기순이익': '당기순이익',
    '지배주주순이익': '당기순이익',  # fallback
    '자산총계': '자산총계',
    '부채총계': '부채총계',
    '자본총계': '자본총계',
    '영업이익률': '영업이익률',
    '순이익률': '순이익률',
    'ROE(%)': 'ROE',
    'ROE': 'ROE',
    'ROA(%)': 'ROA',
    'ROA': 'ROA',
    '부채비율': '부채비율',
    'EPS(원)': 'EPS',
    'EPS': 'EPS',
    'PER(배)': 'PER',
    'PER': 'PER',
    'BPS(원)': 'BPS',
    'BPS': 'BPS',
    'PBR(배)': 'PBR',
    'PBR': 'PBR',
    '주당배당금(원)': '주당배당금',
    '시가배당률(%)': '배당수익률',
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    return conn


def _parse_value(val: str | None) -> float | None:
    if not val or val.strip() in ('-', '', 'N/A'):
        return None
    try:
        return float(val.replace(',', ''))
    except (ValueError, TypeError):
        return None


def _fetch_naver(code: str, period: str = 'annual') -> dict | None:
    """Fetch from Naver Finance API. period: 'annual' or 'quarter'."""
    url = f'{NAVER_API}/{code}/finance/{period}'
    req = Request(url, headers=HEADERS)
    try:
        resp = urlopen(req, timeout=10)
        return json.loads(resp.read())
    except (HTTPError, URLError, json.JSONDecodeError):
        return None


def _save_finance_data(conn: sqlite3.Connection, code: str, data: dict, period_type: str) -> int:
    """Parse Naver response and save to financials table."""
    info = data.get('financeInfo', {})
    periods = info.get('trTitleList', [])
    rows = info.get('rowList', [])
    if not periods or not rows:
        return 0

    saved = 0
    for row in rows:
        title = row.get('title', '').strip()
        metric = METRIC_MAP.get(title)
        if not metric:
            continue
        columns = row.get('columns', {})
        for period_info in periods:
            key = period_info.get('key', '')
            is_consensus = period_info.get('isConsensus') == 'Y'
            if is_consensus:
                continue  # Skip consensus estimates
            cell = columns.get(key, {})
            val = _parse_value(cell.get('value'))
            if val is None:
                continue

            # Convert period key to our format
            # Annual: '202412' -> '2024'
            # Quarter: '202503' -> '2025Q1'
            if period_type == 'annual':
                period_str = key[:4]
            else:
                year = key[:4]
                month = int(key[4:6])
                q = (month - 1) // 3 + 1
                period_str = f'{year}Q{q}'

            conn.execute(
                'INSERT OR REPLACE INTO financials (symbol, period, period_type, metric, value) VALUES (?, ?, ?, ?, ?)',
                (code, period_str, period_type, metric, val),
            )
            saved += 1
    return saved


def main():
    parser = argparse.ArgumentParser(description='Fetch Naver Finance data')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--delay', type=float, default=1.0)
    parser.add_argument('--max-errors', type=int, default=20)
    args = parser.parse_args()

    conn = _connect()
    all_symbols = [r['symbol'] for r in conn.execute('SELECT symbol FROM symbol_meta ORDER BY symbol').fetchall()]
    symbols = all_symbols[args.skip:]
    if args.limit > 0:
        symbols = symbols[:args.limit]

    print(f'Target: {len(symbols)} symbols (skip={args.skip}, total={len(all_symbols)})')
    print(f'Delay: {args.delay}s, Est: {len(symbols) * args.delay * 2 / 60:.0f}min (annual+quarter)')
    print()

    success = 0
    empty = 0
    errors = 0
    consecutive_errors = 0
    start = time.time()

    for i, symbol in enumerate(symbols):
        code = symbol.replace('.KS', '').replace('.KQ', '')

        try:
            # Annual
            annual = _fetch_naver(code, 'annual')
            a_saved = _save_finance_data(conn, code, annual, 'annual') if annual else 0
            time.sleep(args.delay * 0.5)

            # Quarter
            quarter = _fetch_naver(code, 'quarter')
            q_saved = _save_finance_data(conn, code, quarter, 'quarterly') if quarter else 0

            if a_saved + q_saved > 0:
                success += 1
                consecutive_errors = 0
            else:
                empty += 1
        except Exception as e:
            errors += 1
            consecutive_errors += 1
            if consecutive_errors >= args.max_errors:
                print(f'\nSTOPPED: {args.max_errors} consecutive errors. Resume: --skip {args.skip + i}')
                break
            time.sleep(args.delay * 2)
            continue

        if (i + 1) % 50 == 0:
            conn.commit()
            elapsed = time.time() - start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(symbols) - i - 1) / rate if rate > 0 else 0
            print(f'  [{args.skip + i + 1}/{len(all_symbols)}] ok={success} empty={empty} err={errors} {elapsed:.0f}s ~{remaining:.0f}s')

        time.sleep(args.delay)

    conn.commit()
    conn.close()
    elapsed = time.time() - start
    print(f'\nDone in {elapsed:.0f}s: ok={success} empty={empty} errors={errors}')


if __name__ == '__main__':
    main()
