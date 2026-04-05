"""Full Naver Finance data collector — 3-domain parallel.

Collects ALL available financial data from Naver:
  Thread 1 (Mobile API):     integration + finance/annual + finance/quarter + trend
  Thread 2 (NaverComp):      cF3002 (244-item statements) + cF4002 (metrics) + cF9001 (sector)
  Thread 3 (fchart):         1000-day OHLCV (backup, optional)

Saves to data/sepa.db:
  financial_snapshot, financial_statements, financial_metrics,
  sector_comparison, investor_trend, fetch_log

Usage:
    python scripts/fetch_naver_full.py                  # all stocks
    python scripts/fetch_naver_full.py --limit 50       # test
    python scripts/fetch_naver_full.py --skip 500       # resume
    python scripts/fetch_naver_full.py --source mobile  # mobile only
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / 'data' / 'sepa.db'
MOBILE_API = 'https://m.stock.naver.com/api/stock'
COMP_BASE = 'https://navercomp.wisereport.co.kr/v2/company'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    return conn


def _fetch_json(url: str, session: requests.Session | None = None, timeout: int = 10) -> dict | list | None:
    try:
        if session:
            resp = session.get(url, timeout=timeout)
            if resp.ok:
                return resp.json()
            return None
        req = Request(url, headers=HEADERS)
        return json.loads(urlopen(req, timeout=timeout).read())
    except Exception:
        return None


def _parse_num(s) -> float | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    v = str(s).replace(',', '').strip()
    # Strip Korean unit suffixes: 배, 원, %, 조, 억, 만, 주
    for suffix in ('배', '원', '%', '조', '억', '만', '주', '백만'):
        v = v.rstrip(suffix)
    v = v.replace('+', '').strip()
    if not v or v in ('-', 'N/A', ''):
        return None
    try:
        return float(v)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Thread 1: Mobile API
# ---------------------------------------------------------------------------

def fetch_mobile(code: str, conn: sqlite3.Connection) -> dict:
    """Fetch integration + finance/annual + finance/quarter + trend."""
    stats = {'integration': False, 'finance': 0, 'trend': 0}
    session = requests.Session()
    session.headers.update(HEADERS)
    now = datetime.now().isoformat(timespec='seconds')

    # 1. Integration (snapshot)
    data = _fetch_json(f'{MOBILE_API}/{code}/integration', session)
    if data and isinstance(data, dict):
        # Keys are Korean labels, not English field names
        infos = {}
        for it in data.get('totalInfos', []):
            k = (it.get('key') or '').strip()
            v = (it.get('value') or '').strip()
            infos[k] = v
        consensus = data.get('consensusInfo') or {}

        # Parse Korean market cap text: "1,102조 2,366억" → KRW
        mktcap_text = infos.get('시총', '') or infos.get('marketValue', '')
        mktcap_krw = None
        if mktcap_text:
            import re as _re
            total_krw = 0.0
            m_jo = _re.search(r'([\d,.]+)\s*조', mktcap_text)
            m_eok = _re.search(r'([\d,.]+)\s*억', mktcap_text)
            if m_jo:
                total_krw += float(m_jo.group(1).replace(',', '')) * 1_000_000_000_000
            if m_eok:
                total_krw += float(m_eok.group(1).replace(',', '')) * 100_000_000
            if total_krw > 0:
                mktcap_krw = total_krw

        conn.execute('''INSERT OR REPLACE INTO financial_snapshot
            (symbol, price, market_cap_krw, per, eps, pbr, bps, roe,
             cns_per, cns_eps, target_price, recommend_score,
             dividend_yield, dividend, foreign_ratio, high_52w, low_52w,
             updated_at, source)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
            code,
            _parse_num(infos.get('전일') or infos.get('closePrice')),
            mktcap_krw,
            _parse_num(infos.get('PER')),
            _parse_num(infos.get('EPS')),
            _parse_num(infos.get('PBR')),
            _parse_num(infos.get('BPS')),
            None,  # ROE comes from finance API
            _parse_num(infos.get('추정PER')),
            _parse_num(infos.get('추정EPS')),
            _parse_num(consensus.get('priceTargetMean')),
            _parse_num(consensus.get('recommMean')),
            _parse_num(infos.get('배당수익률')),
            _parse_num(infos.get('주당배당금')),
            _parse_num(infos.get('외인소진율') or infos.get('외국인소진율')),
            _parse_num(infos.get('52주 최고')),
            _parse_num(infos.get('52주 최저')),
            now, 'naver_mobile',
        ))
        stats['integration'] = True

    time.sleep(0.2)

    # 2. Finance annual + quarter (→ existing financials table for backward compat)
    for ptype, ep in [('annual', 'finance/annual'), ('quarterly', 'finance/quarter')]:
        fdata = _fetch_json(f'{MOBILE_API}/{code}/{ep}', session)
        if not fdata or not isinstance(fdata, dict):
            continue
        info = fdata.get('financeInfo', {})
        periods = info.get('trTitleList', [])
        for row in info.get('rowList', []):
            title = (row.get('title') or '').strip()
            if not title:
                continue
            columns = row.get('columns', {})
            for pi in periods:
                if pi.get('isConsensus') == 'Y':
                    continue
                key = pi.get('key', '')
                cell = columns.get(key, {})
                val = _parse_num(cell.get('value'))
                if val is None:
                    continue
                if ptype == 'annual':
                    period = key[:4]
                else:
                    year = key[:4]
                    month = int(key[4:6]) if len(key) >= 6 else 12
                    period = f'{year}Q{(month - 1) // 3 + 1}'
                conn.execute(
                    'INSERT OR REPLACE INTO financials (symbol, period, period_type, metric, value) VALUES (?,?,?,?,?)',
                    (code, period, ptype, title, val),
                )
                stats['finance'] += 1
        time.sleep(0.2)

    # 3. Trend (investor flow)
    tdata = _fetch_json(f'{MOBILE_API}/{code}/trend', session)
    if tdata and isinstance(tdata, list):
        for item in tdata:
            trade_date = str(item.get('bizdate') or '').strip()
            if not trade_date:
                continue
            conn.execute('''INSERT OR REPLACE INTO investor_trend
                (symbol, trade_date, foreign_net, foreign_ratio, institution_net,
                 individual_net, close_price, volume)
                VALUES (?,?,?,?,?,?,?,?)''', (
                code, trade_date,
                _parse_num(item.get('foreignerPureBuyQuant')),
                _parse_num(item.get('foreignerHoldRatio')),
                _parse_num(item.get('organPureBuyQuant')),
                _parse_num(item.get('individualPureBuyQuant')),
                _parse_num(item.get('closePrice')),
                _parse_num(item.get('accumulatedTradingVolume')),
            ))
            stats['trend'] += 1

    session.close()
    return stats


# ---------------------------------------------------------------------------
# Thread 2: NaverComp (cF3002 + cF4002 + cF9001)
# ---------------------------------------------------------------------------

def _get_encparam(session: requests.Session, code: str) -> str | None:
    """Get session-based encparam token from NaverComp."""
    url = f'{COMP_BASE}/c1030001.aspx?cmp_cd={code}'
    try:
        resp = session.get(url, timeout=15)
        if not resp.ok:
            return None
        matches = re.findall(r'encparam[^a-zA-Z0-9]*([a-zA-Z0-9+/=]{10,})', resp.text)
        return matches[0] if matches else None
    except Exception:
        return None


def fetch_navercomp(code: str, conn: sqlite3.Connection) -> dict:
    """Fetch cF3002 (statements) + cF4002 (metrics) + cF9001 (sector)."""
    stats = {'statements': 0, 'metrics': 0, 'sector': 0}
    session = requests.Session()
    session.headers.update({
        'User-Agent': HEADERS['User-Agent'],
        'Referer': f'{COMP_BASE}/c1030001.aspx?cmp_cd={code}',
    })

    enc = _get_encparam(session, code)
    if not enc:
        session.close()
        return stats

    # 1. cF3002 — 244-item financial statements (IS+BS+CF)
    for freq, freq_label in [('Y', 'annual'), ('Q', 'quarterly')]:
        url = f'{COMP_BASE}/cF3002.aspx?cmp_cd={code}&frq_typ={freq}&rpt_typ=ISM&encparam={enc}'
        data = _fetch_json(url, session, timeout=20)
        if not data or not isinstance(data, dict):
            continue
        periods_raw = data.get('YYMM', [])
        rows = data.get('DATA', [])

        # Parse period labels: "2024/12 (IFRS연결)" → "2024", "2024/12(E)" → estimate
        periods = []
        for p in periods_raw:
            clean = re.sub(r'<br\s*/?>', ' ', str(p)).strip()
            is_est = '(E)' in clean
            # Extract year or year/quarter
            m = re.match(r'(\d{4})/(\d{2})', clean)
            if m:
                year, month = m.group(1), int(m.group(2))
                if freq == 'Y':
                    period_str = year
                else:
                    period_str = f'{year}Q{(month - 1) // 3 + 1}'
                periods.append((period_str, is_est))

        for row in rows:
            acc_name = (row.get('ACC_NM') or '').strip()
            acc_code = str(row.get('ACCODE') or '')
            level = row.get('LVL', 1)
            if not acc_name:
                continue

            for i, (period_str, is_est) in enumerate(periods):
                data_key = f'DATA{i + 1}'
                val = row.get(data_key)
                if val is None:
                    continue
                try:
                    val_f = float(val)
                except (ValueError, TypeError):
                    continue

                yoy_val = row.get('YYOY') if i == len(periods) - 2 else None

                conn.execute('''INSERT OR REPLACE INTO financial_statements
                    (symbol, period, period_type, account_code, account_name,
                     account_level, value, yoy, is_estimate, source)
                    VALUES (?,?,?,?,?,?,?,?,?,?)''', (
                    code, period_str, freq_label, acc_code, acc_name,
                    level, val_f, _parse_num(yoy_val), 1 if is_est else 0,
                    'naver_comp',
                ))
                stats['statements'] += 1
        time.sleep(0.3)

    # 2. cF4002 — Investment metrics (ROA, ROIC, EBITDA margin)
    url = f'{COMP_BASE}/cF4002.aspx?cmp_cd={code}&frq_typ=Y&encparam={enc}'
    mdata = _fetch_json(url, session, timeout=15)
    if mdata and isinstance(mdata, dict):
        periods_raw = mdata.get('YYMM', [])
        m_periods = []
        for p in periods_raw:
            clean = re.sub(r'<br\s*/?>', ' ', str(p)).strip()
            m2 = re.match(r'(\d{4})', clean)
            if m2:
                m_periods.append(m2.group(1))

        for row in mdata.get('DATA', []):
            metric_name = (row.get('ACC_NM') or '').strip()
            if not metric_name:
                continue
            for i, period_str in enumerate(m_periods):
                val = row.get(f'DATA{i + 1}')
                if val is None:
                    continue
                try:
                    val_f = float(val)
                except (ValueError, TypeError):
                    continue
                conn.execute('''INSERT OR REPLACE INTO financial_metrics
                    (symbol, period, metric, value, source)
                    VALUES (?,?,?,?,?)''', (
                    code, period_str, metric_name, val_f, 'naver_comp',
                ))
                stats['metrics'] += 1
    time.sleep(0.3)

    # 3. cF9001 — Sector comparison
    url = f'{COMP_BASE}/ajax/cF9001.aspx?cmp_cd={code}&data_typ=1&sec_cd=&chartType=svg'
    sdata = _fetch_json(url, session, timeout=15)
    if sdata and isinstance(sdata, dict):
        now = datetime.now().isoformat(timespec='seconds')
        dt3 = sdata.get('dt3') or sdata.get('dt0')
        if dt3 and isinstance(dt3, dict):
            for row in dt3.get('data', []):
                item = str(row.get('ITEM', ''))
                gubn = str(row.get('GUBN', ''))
                # Map ITEM codes to metric names
                item_map = {'3': 'revenue_growth', '6': 'debt_ratio', '8': 'dividend_yield',
                            '9': 'roe', '11': 'gross_margin'}
                metric = item_map.get(item)
                if not metric:
                    continue
                val = _parse_num(row.get('FY0'))
                if val is None:
                    continue
                if gubn == '1':  # company
                    conn.execute('''INSERT OR REPLACE INTO sector_comparison
                        (symbol, metric, company_value, period, updated_at)
                        VALUES (?,?,?,?,?)''', (code, metric, val, '', now))
                elif gubn == '2':  # sector
                    conn.execute('''UPDATE sector_comparison SET sector_value=?
                        WHERE symbol=? AND metric=?''', (val, code, metric))
                elif gubn == '3':  # market
                    conn.execute('''UPDATE sector_comparison SET market_value=?
                        WHERE symbol=? AND metric=?''', (val, code, metric))
                stats['sector'] += 1

    session.close()
    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def process_one(code: str, sources: set[str]) -> dict:
    """Process one stock across all sources."""
    conn = _connect()
    now = datetime.now().isoformat(timespec='seconds')
    result = {'code': code, 'ok': False}

    try:
        if 'mobile' in sources:
            m_stats = fetch_mobile(code, conn)
            conn.execute('INSERT OR REPLACE INTO fetch_log VALUES (?,?,?,?,?,?)',
                         (code, 'mobile', 'ok' if m_stats['integration'] else 'empty',
                          now, None, m_stats['finance']))
            result['mobile'] = m_stats

        if 'comp' in sources:
            c_stats = fetch_navercomp(code, conn)
            conn.execute('INSERT OR REPLACE INTO fetch_log VALUES (?,?,?,?,?,?)',
                         (code, 'navercomp', 'ok' if c_stats['statements'] > 0 else 'empty',
                          now, None, c_stats['statements']))
            result['comp'] = c_stats

        conn.commit()
        result['ok'] = True
    except Exception as e:
        conn.execute('INSERT OR REPLACE INTO fetch_log VALUES (?,?,?,?,?,?)',
                     (code, 'error', 'fail', now, str(e)[:200], 0))
        conn.commit()
        result['error'] = str(e)
    finally:
        conn.close()

    return result


def main():
    parser = argparse.ArgumentParser(description='Full Naver Finance data collector')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--skip', type=int, default=0)
    parser.add_argument('--source', choices=['all', 'mobile', 'comp'], default='all')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--delay', type=float, default=0.3)
    args = parser.parse_args()

    sources = {'mobile', 'comp'} if args.source == 'all' else {args.source}

    conn = _connect()
    all_symbols = [r['symbol'] for r in conn.execute('SELECT symbol FROM symbol_meta ORDER BY symbol').fetchall()]

    # Skip already-done symbols
    done_mobile = set(r[0] for r in conn.execute("SELECT symbol FROM fetch_log WHERE source='mobile' AND status='ok'").fetchall()) if 'mobile' in sources else set()
    done_comp = set(r[0] for r in conn.execute("SELECT symbol FROM fetch_log WHERE source='navercomp' AND status='ok'").fetchall()) if 'comp' in sources else set()
    done = done_mobile & done_comp if len(sources) > 1 else (done_mobile | done_comp)
    conn.close()

    todo = [s for s in all_symbols if s not in done]
    todo = todo[args.skip:]
    if args.limit > 0:
        todo = todo[:args.limit]

    total = len(todo)
    print(f'Target: {total} stocks (skip={args.skip}, done={len(done)}/{len(all_symbols)})', flush=True)
    print(f'Sources: {sources}, Workers: {args.workers}', flush=True)

    ok = 0
    err = 0
    t0 = time.time()

    # Process with thread pool — each thread handles one stock across all sources
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for i, code in enumerate(todo):
            f = executor.submit(process_one, code, sources)
            futures[f] = (i, code)
            time.sleep(args.delay)  # stagger submissions

        for f in as_completed(futures):
            i, code = futures[f]
            try:
                result = f.result()
                if result.get('ok'):
                    ok += 1
                else:
                    err += 1
            except Exception:
                err += 1

            done_count = ok + err
            if done_count % 50 == 0:
                elapsed = time.time() - t0
                rate = done_count / elapsed if elapsed > 0 else 1
                remain = (total - done_count) / rate if rate > 0 else 0
                print(f'  [{done_count}/{total}] ok={ok} err={err} {elapsed:.0f}s ~{remain:.0f}s', flush=True)

    elapsed = time.time() - t0
    print(f'\nDONE {elapsed:.0f}s: ok={ok} err={err}', flush=True)


if __name__ == '__main__':
    main()
