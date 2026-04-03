"""Comprehensive Naver Finance data fetcher.

Fetches ALL available data per stock:
1. Basic info (price, name, market)
2. Integration (totalInfos: 시총/PER/EPS/PBR/외인비율/52주/컨센서스)
3. Annual financials (매출/영업이익/순이익/자산/부채/자본 + 비율)
4. Quarterly financials (same, per quarter)
5. Corporation summary (기업 개요)

Saves everything to ohlcv.db: symbol_meta + financials tables.

Usage:
    python scripts/fetch_naver_all.py --limit 50   # test
    python scripts/fetch_naver_all.py              # all (~96min)
    python scripts/fetch_naver_all.py --skip 500   # resume
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

DB_PATH = PROJECT_ROOT / '.omx' / 'artifacts' / 'ohlcv.db'
NAVER_API = 'https://m.stock.naver.com/api/stock'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

METRIC_MAP = {
    '매출액': '매출액', '영업이익': '영업이익', '당기순이익': '당기순이익',
    '지배주주순이익': '당기순이익', '자산총계': '자산총계', '부채총계': '부채총계',
    '자본총계': '자본총계', '영업이익률': '영업이익률', '순이익률': '순이익률',
    'ROE(%)': 'ROE', 'ROE': 'ROE', 'ROA(%)': 'ROA', 'ROA': 'ROA',
    '부채비율': '부채비율', 'EPS(원)': 'EPS', 'EPS': 'EPS',
    'PER(배)': 'PER', 'PER': 'PER', 'BPS(원)': 'BPS', 'BPS': 'BPS',
    'PBR(배)': 'PBR', 'PBR': 'PBR', '주당배당금(원)': '주당배당금',
    '시가배당률(%)': '배당수익률',
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    return conn


def _ensure_columns(conn: sqlite3.Connection) -> None:
    existing = {r[1] for r in conn.execute('PRAGMA table_info(symbol_meta)').fetchall()}
    new_cols = {
        'market_cap': 'TEXT', 'foreign_ratio': 'TEXT', 'high_52w': 'TEXT', 'low_52w': 'TEXT',
        'consensus_target': 'TEXT', 'consensus_opinion': 'REAL',
        'per': 'REAL', 'eps': 'REAL', 'pbr': 'REAL', 'bps': 'REAL', 'roe': 'REAL',
        'est_per': 'TEXT', 'est_eps': 'TEXT', 'dividend_yield': 'TEXT',
        'description': 'TEXT', 'revenue': 'REAL', 'op_profit': 'REAL', 'net_income': 'REAL',
    }
    for col, ctype in new_cols.items():
        if col not in existing:
            try:
                conn.execute(f'ALTER TABLE symbol_meta ADD COLUMN {col} {ctype}')
            except sqlite3.OperationalError:
                pass
    conn.commit()


def _fetch(url: str) -> dict | None:
    try:
        req = Request(url, headers=HEADERS)
        resp = urlopen(req, timeout=10)
        return json.loads(resp.read())
    except (HTTPError, URLError, json.JSONDecodeError):
        return None


def _parse_val(s: str | None) -> str:
    return (s or '').replace(',', '').strip()


def _parse_float(s: str | None) -> float | None:
    v = _parse_val(s)
    if not v or v in ('-', 'N/A', ''):
        return None
    try:
        return float(v.replace('배', '').replace('원', '').replace('%', '').replace('조', '').replace('억', ''))
    except (ValueError, TypeError):
        return None


def _fetch_and_save(conn: sqlite3.Connection, code: str, symbol: str) -> dict:
    """Fetch all data for one stock. Returns stats."""
    stats = {'basic': False, 'integration': False, 'annual': 0, 'quarterly': 0}

    # 1. Integration (richest single endpoint)
    integ = _fetch(f'{NAVER_API}/{code}/integration')
    if integ:
        stats['integration'] = True
        infos = {i.get('key', ''): i.get('value', '') for i in integ.get('totalInfos', [])}
        consensus = integ.get('consensusInfo') or {}

        updates = {}
        if infos.get('시가총액'):
            updates['market_cap'] = infos['시가총액']
        if infos.get('외국인비율'):
            updates['foreign_ratio'] = infos['외국인비율']
        if infos.get('52주 최고'):
            updates['high_52w'] = _parse_val(infos['52주 최고'])
        if infos.get('52주 최저'):
            updates['low_52w'] = _parse_val(infos['52주 최저'])
        if infos.get('PER'):
            updates['per'] = _parse_float(infos['PER'])
        if infos.get('EPS'):
            updates['eps'] = _parse_float(infos['EPS'])
        if infos.get('PBR'):
            updates['pbr'] = _parse_float(infos['PBR'])
        if infos.get('BPS'):
            updates['bps'] = _parse_float(infos['BPS'])
        if infos.get('추정PER'):
            updates['est_per'] = infos['추정PER']
        if infos.get('추정EPS'):
            updates['est_eps'] = infos['추정EPS']
        if infos.get('배당수익률'):
            updates['dividend_yield'] = infos['배당수익률']
        if consensus.get('priceTargetMean'):
            updates['consensus_target'] = str(consensus['priceTargetMean'])
        if consensus.get('recommMean'):
            updates['consensus_opinion'] = float(consensus['recommMean'])

        if updates:
            sets = ', '.join(f'{k} = ?' for k in updates)
            vals = list(updates.values()) + [symbol]
            conn.execute(f'UPDATE symbol_meta SET {sets} WHERE symbol = ?', vals)

    time.sleep(0.3)

    # 2. Corporation summary (from finance/annual)
    annual_data = _fetch(f'{NAVER_API}/{code}/finance/annual')
    if annual_data:
        cs = annual_data.get('corporationSummary') or {}
        if cs:
            desc_parts = []
            for k in ('businessSummary', 'companyOverview', 'mainProduct'):
                v = cs.get(k)
                if v:
                    desc_parts.append(str(v))
            if desc_parts:
                conn.execute('UPDATE symbol_meta SET description = ? WHERE symbol = ?',
                             ('\n'.join(desc_parts)[:2000], symbol))

        # Save annual financials
        stats['annual'] = _save_financials(conn, code, annual_data, 'annual')

    time.sleep(0.3)

    # 3. Quarterly
    quarter_data = _fetch(f'{NAVER_API}/{code}/finance/quarter')
    if quarter_data:
        stats['quarterly'] = _save_financials(conn, code, quarter_data, 'quarterly')

    return stats


def _save_financials(conn: sqlite3.Connection, code: str, data: dict, period_type: str) -> int:
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
        for pi in periods:
            if pi.get('isConsensus') == 'Y':
                continue
            key = pi.get('key', '')
            cell = columns.get(key, {})
            val = _parse_float(cell.get('value'))
            if val is None:
                continue
            if period_type == 'annual':
                period_str = key[:4]
            else:
                year = key[:4]
                month = int(key[4:6]) if len(key) >= 6 else 12
                q = (month - 1) // 3 + 1
                period_str = f'{year}Q{q}'
            conn.execute(
                'INSERT OR REPLACE INTO financials (symbol, period, period_type, metric, value) VALUES (?, ?, ?, ?, ?)',
                (code, period_str, period_type, metric, val),
            )
            saved += 1
    return saved


def main():
    parser = argparse.ArgumentParser(description='Fetch ALL Naver Finance data')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--delay', type=float, default=1.0)
    parser.add_argument('--max-errors', type=int, default=20)
    args = parser.parse_args()

    conn = _connect()
    _ensure_columns(conn)

    all_symbols = [(r['symbol'],) for r in conn.execute('SELECT symbol FROM symbol_meta ORDER BY symbol').fetchall()]
    symbols = all_symbols[args.skip:]
    if args.limit > 0:
        symbols = symbols[:args.limit]

    total = len(symbols)
    print(f'Target: {total} (skip={args.skip}, total={len(all_symbols)})')
    print(f'Delay: {args.delay}s, Est: {total * args.delay * 2 / 60:.0f}min')
    print(f'Data: integration(시총/PER/외인) + annual + quarterly + 기업개요')
    print()

    ok = 0
    empty = 0
    errors = 0
    consec_err = 0
    start = time.time()

    for i, (symbol,) in enumerate(symbols):
        code = symbol.replace('.KS', '').replace('.KQ', '')
        try:
            stats = _fetch_and_save(conn, code, symbol)
            if stats['annual'] > 0 or stats['integration']:
                ok += 1
                consec_err = 0
            else:
                empty += 1
        except Exception as e:
            errors += 1
            consec_err += 1
            if consec_err >= args.max_errors:
                print(f'\nSTOPPED at {args.skip + i}. Resume: --skip {args.skip + i}')
                break
            time.sleep(args.delay * 2)
            continue

        if (i + 1) % 50 == 0:
            conn.commit()
            el = time.time() - start
            rate = (i + 1) / el if el > 0 else 0
            rem = (total - i - 1) / rate if rate > 0 else 0
            print(f'  [{args.skip + i + 1}/{len(all_symbols)}] ok={ok} empty={empty} err={errors} {el:.0f}s ~{rem:.0f}s')

        time.sleep(args.delay)

    conn.commit()
    conn.close()
    el = time.time() - start
    print(f'\nDone {el:.0f}s: ok={ok} empty={empty} errors={errors}')


if __name__ == '__main__':
    main()
