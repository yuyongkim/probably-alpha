"""Fetch financial statements from DART OpenAPI for all matched stocks.

Usage:
    python scripts/fetch_dart_financials.py              # all (slow, ~46min)
    python scripts/fetch_dart_financials.py --limit 50   # test 50
    python scripts/fetch_dart_financials.py --skip 500   # resume
    python scripts/fetch_dart_financials.py --delay 1.5  # slower
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / '.env'
DB_PATH = PROJECT_ROOT / 'data' / 'meta.db'
DART_BASE = 'https://opendart.fss.or.kr/api'


def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env(ENV_PATH)
sys.path.insert(0, str(PROJECT_ROOT))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=DELETE')
    conn.execute('PRAGMA busy_timeout=30000')
    return conn


def _get_matched_symbols(conn: sqlite3.Connection) -> list[dict]:
    """Get symbols that have both ohlcv data and DART corp_code."""
    return [dict(r) for r in conn.execute('''
        SELECT m.symbol, d.corp_code, d.corp_name
        FROM symbol_meta m
        JOIN dart_corp_code d ON REPLACE(m.symbol, '.KS', '') = d.stock_code
           OR REPLACE(m.symbol, '.KQ', '') = d.stock_code
        ORDER BY m.symbol
    ''').fetchall()]


def _fetch_dart_financials(api_key: str, corp_code: str, year: str, report_code: str = '11011') -> list[dict]:
    """Fetch single company financials from DART.

    report_code:
      11011 = 사업보고서 (연간)
      11012 = 반기보고서
      11013 = 1분기보고서
      11014 = 3분기보고서
    """
    params = urlencode({
        'crtfc_key': api_key,
        'corp_code': corp_code,
        'bsns_year': year,
        'reprt_code': report_code,
    })
    url = f'{DART_BASE}/fnlttSinglAcnt.json?{params}'
    try:
        resp = urlopen(url, timeout=15)
        data = json.loads(resp.read())
        if data.get('status') == '000':
            return data.get('list', [])
    except (HTTPError, URLError, json.JSONDecodeError):
        pass
    return []


# DART account_nm -> our metric key
ACCOUNT_MAP = {
    '매출액': 'revenue',
    '영업이익': 'op_profit',
    '당기순이익': 'net_income',
    '자산총계': 'total_asset',
    '부채총계': 'total_debt',
    '자본총계': 'equity',
}


def _parse_amount(val: str | None) -> float | None:
    if not val:
        return None
    try:
        return float(val.replace(',', ''))
    except (ValueError, TypeError):
        return None


def _save_financials(conn: sqlite3.Connection, symbol: str, items: list[dict], year: str, period_type: str = 'annual') -> int:
    """Parse DART response and save to financials table. Returns count."""
    saved = 0
    code = symbol.replace('.KS', '').replace('.KQ', '')
    for item in items:
        account = item.get('account_nm', '')
        metric_key = ACCOUNT_MAP.get(account)
        if not metric_key:
            continue
        # Use thstrm_amount (당기금액) in 원 단위
        raw = item.get('thstrm_amount')
        val = _parse_amount(raw)
        if val is None:
            continue
        # Convert to 억원
        val_eok = val / 100_000_000
        conn.execute(
            'INSERT OR REPLACE INTO financials (symbol, period, period_type, metric, value) VALUES (?, ?, ?, ?, ?)',
            (code, year, period_type, account, round(val_eok, 2)),
        )
        saved += 1
    return saved


def main():
    parser = argparse.ArgumentParser(description='Fetch DART financials')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--delay', type=float, default=1.0, help='Seconds between calls')
    parser.add_argument('--year', type=str, default='2024', help='Fiscal year')
    parser.add_argument('--max-errors', type=int, default=15)
    args = parser.parse_args()

    api_key = os.getenv('DART_API_KEY', '')
    if not api_key:
        print('ERROR: DART_API_KEY not set')
        sys.exit(1)
    print(f'DART API key: {api_key[:8]}...')

    conn = _connect()
    all_matched = _get_matched_symbols(conn)
    symbols = all_matched[args.skip:]
    if args.limit > 0:
        symbols = symbols[:args.limit]

    print(f'Target: {len(symbols)} symbols (skip={args.skip}, total matched={len(all_matched)})')
    print(f'Year: {args.year}, Delay: {args.delay}s, Est: {len(symbols) * args.delay / 60:.1f}min')
    print()

    success = 0
    empty = 0
    errors = 0
    consecutive_errors = 0
    start = time.time()

    for i, row in enumerate(symbols):
        symbol = row['symbol']
        corp_code = row['corp_code']

        try:
            items = _fetch_dart_financials(api_key, corp_code, args.year)
        except Exception as e:
            print(f'  ERROR {symbol}: {e}')
            errors += 1
            consecutive_errors += 1
            if consecutive_errors >= args.max_errors:
                print(f'\nSTOPPED: {args.max_errors} consecutive errors. Resume: --skip {args.skip + i}')
                break
            time.sleep(args.delay * 3)
            continue

        consecutive_errors = 0

        if not items:
            empty += 1
        else:
            saved = _save_financials(conn, symbol, items, args.year)
            if saved > 0:
                success += 1
            else:
                empty += 1

        if (i + 1) % 50 == 0:
            conn.commit()
            elapsed = time.time() - start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(symbols) - i - 1) / rate if rate > 0 else 0
            print(f'  [{args.skip + i + 1}/{len(all_matched)}] ok={success} empty={empty} err={errors} {elapsed:.0f}s ~{remaining:.0f}s left')

        time.sleep(args.delay)

    conn.commit()
    conn.close()
    elapsed = time.time() - start
    print(f'\nDone in {elapsed:.0f}s: ok={success} empty={empty} errors={errors}')


if __name__ == '__main__':
    main()
