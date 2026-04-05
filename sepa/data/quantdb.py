"""QuantDB reader — used ONLY for:
  - Universe listing (read_universe)
  - Supplementary metrics not in Naver (ROA, EV/EBITDA, f_score, foreign_1m)
  - Legacy price data (read_price_rows)

All financial metrics (PER, EPS, ROE, revenue, etc.) come from
sepa/data/naver_financials.py via data/financial.db.
"""
from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path

from sepa.data.symbols import to_kiwoom_symbol

# ── Re-exports from quantdb_layout ──────────────────────────────────────────
from sepa.data.quantdb_layout import (  # noqa: F401
    DEFAULT_BACKUP_DB,
    DEFAULT_HISTORY_SUFFIX,
    DEFAULT_MAIN_DB,
    DEFAULT_SNAPSHOT_SUFFIX,
    QuantDbLayout,
    _table_exists,
    resolve_quantdb_layout,
    resolve_quantdb_path,
)

# ── Re-export for backward compatibility ──────────────────────────────────
# financial_summary now comes from naver_financials; this re-export
# is kept only for callers that haven't been migrated yet.
def read_financial_summary(symbol: str, **kwargs) -> dict:
    from sepa.data.naver_financials import read_financial_series
    return read_financial_series(symbol, **kwargs)


# ── Local helpers ────────────────────────────────────────────────────────────

def _connect(path: Path | None) -> sqlite3.Connection | None:
    if not path or not path.exists() or not path.is_file() or path.stat().st_size <= 0:
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _latest_run_id(conn: sqlite3.Connection, table: str) -> str | None:
    if not _table_exists(conn, table):
        return None
    row = conn.execute(
        f'''
        select run_id
        from {table}
        where run_id is not null and trim(run_id) <> ''
        order by id desc
        limit 1
        '''
    ).fetchone()
    return str(row['run_id']).strip() if row and row['run_id'] else None


def _normalize_market_suffix(market: str) -> str:
    raw = str(market or '').strip().upper().replace(' ', '')
    if raw in {'코스닥', 'KOSDAQ', 'KQ'}:
        return '.KQ'
    if raw in {'코넥스', 'KONEX', 'KN'}:
        return '.KN'
    return '.KS'


def _symbol_from_code(code: str, market: str) -> str:
    digits = to_kiwoom_symbol(code)
    if not digits or not digits.isdigit():
        return str(code or '').strip().upper()
    return f'{digits}{_normalize_market_suffix(market)}'


def _market_matches(raw_market: str, markets: tuple[str, ...]) -> bool:
    if not markets:
        return True
    normalized = str(raw_market or '').strip().upper().replace(' ', '')
    aliases = {normalized}
    if normalized in {'코스피', 'KOSPI', 'KS'}:
        aliases.update({'코스피', 'KOSPI', 'KS'})
    elif normalized in {'코스닥', 'KOSDAQ', 'KQ'}:
        aliases.update({'코스닥', 'KOSDAQ', 'KQ'})
    elif normalized in {'코넥스', 'KONEX', 'KN'}:
        aliases.update({'코넥스', 'KONEX', 'KN'})
    return any(str(market or '').strip().upper().replace(' ', '') in aliases for market in markets)


def _quarter_period(year: str, quarter: str) -> str:
    y = str(year or '').strip()
    q = str(quarter or '').strip().upper()
    if y.isdigit() and q in {'Q1', 'Q2', 'Q3', 'Q4'}:
        return f'{y}{q}'
    return ''


def _quarter_available_token(year: str, quarter: str) -> str:
    y = str(year or '').strip()
    q = str(quarter or '').strip().upper()
    if not y.isdigit() or q not in {'Q1', 'Q2', 'Q3', 'Q4'}:
        return ''
    year_num = int(y)
    mapping = {
        'Q1': ('0331', 45),
        'Q2': ('0630', 45),
        'Q3': ('0930', 45),
        'Q4': ('1231', 75),
    }
    month_day, lag = mapping[q]
    from datetime import date, timedelta

    quarter_end = date.fromisoformat(f'{year_num}-{month_day[:2]}-{month_day[2:]}')
    return (quarter_end + timedelta(days=lag)).strftime('%Y%m%d')


def _preferred_quant_table(conn: sqlite3.Connection) -> str | None:
    for candidate in ('quantking_snapshot', 'tickers'):
        if _table_exists(conn, candidate):
            count = conn.execute(f'select count(*) as cnt from {candidate}').fetchone()['cnt']
            if count:
                return candidate
    return None


# ── Public API ───────────────────────────────────────────────────────────────

def health() -> dict:
    layout = resolve_quantdb_layout()
    payload = {
        'path': '',
        'available': False,
        'project_dir': '',
        'main_path': '',
        'snapshot_path': '',
        'history_path': '',
        'has_prices': False,
        'has_tickers': False,
        'has_quantking_snapshot': False,
        'has_financials_quarterly': False,
    }
    if not layout:
        return payload

    payload.update(
        {
            'path': str(layout.main or ''),
            'available': bool(layout.main),
            'project_dir': str(layout.project_dir),
            'main_path': str(layout.main or ''),
            'snapshot_path': str(layout.snapshot or ''),
            'history_path': str(layout.history or ''),
        }
    )

    for attr, key, tables in (
        ('main', 'has_prices', ('prices', 'price_daily')),
        ('main', 'has_tickers', ('tickers',)),
        ('main', 'has_quantking_snapshot', ('quantking_snapshot',)),
        ('snapshot', 'has_financials_quarterly', ('financials_quarterly',)),
    ):
        path = getattr(layout, attr)
        try:
            with sqlite3.connect(path) as conn:  # type: ignore[arg-type]
                payload[key] = any(_table_exists(conn, table) for table in tables)
        except sqlite3.Error:
            payload[key] = False
    return payload


@lru_cache(maxsize=16)
def _cached_universe(limit: int, markets_key: str) -> tuple[dict[str, str], ...]:
    layout = resolve_quantdb_layout()
    if not layout or not layout.main:
        return tuple()

    markets = tuple(part.strip() for part in markets_key.split('|') if part.strip())
    conn = _connect(layout.main)
    if conn is None:
        return tuple()

    try:
        table = _preferred_quant_table(conn)
        if not table:
            return tuple()
        run_id = _latest_run_id(conn, table)
        params: list[object] = []
        where_parts: list[str] = []
        if run_id:
            where_parts.append('run_id = ?')
            params.append(run_id)
        where_sql = f"where {' and '.join(where_parts)}" if where_parts else ''
        order_sql = 'order by coalesce(mkt_cap, 0) desc, code asc' if table == 'quantking_snapshot' else 'order by code asc'
        rows = conn.execute(
            f'''
            select
              code,
              company,
              market,
              coalesce(sector_large, sector_small, market, 'Other') as sector_large,
              coalesce(sector_small, sector_large, market, 'Other') as sector_small,
              coalesce(mkt_cap, 0) as mkt_cap
            from {table}
            {where_sql}
            {order_sql}
            ''',
            tuple(params),
        ).fetchall()
    except sqlite3.Error:
        conn.close()
        return tuple()
    finally:
        conn.close()

    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if not _market_matches(str(row['market'] or ''), markets):
            continue
        symbol = _symbol_from_code(str(row['code'] or ''), str(row['market'] or ''))
        if not symbol or symbol in seen:
            continue
        out.append(
            {
                'symbol': symbol,
                'name': str(row['company'] or symbol).strip() or symbol,
                'sector': str(row['sector_large'] or 'Other').strip() or 'Other',
                'sector_group': str(row['sector_large'] or 'Other').strip() or 'Other',
                'industry': str(row['sector_small'] or row['sector_large'] or 'Other').strip() or 'Other',
                'sample_profile': 'steady',
                'eps_profile': 'positive_growth',
            }
        )
        seen.add(symbol)
        if limit > 0 and len(out) >= limit:
            break
    return tuple(out)


def read_universe(*, limit: int = 0, markets: tuple[str, ...] = ()) -> list[dict[str, str]]:
    return [dict(row) for row in _cached_universe(int(limit), '|'.join(markets))]


def read_price_rows(symbol: str) -> list[dict]:
    layout = resolve_quantdb_layout()
    if not layout:
        return []

    for path, candidate_tables in (
        (layout.history, ('price_daily',)),
        (layout.main, ('prices',)),
        (layout.backup, ('prices', 'price_daily')),
    ):
        conn = _connect(path)
        if conn is None:
            continue
        try:
            table = None
            for candidate in candidate_tables:
                if _table_exists(conn, candidate):
                    count = conn.execute(f'select count(*) as cnt from {candidate}').fetchone()['cnt']
                    if count:
                        table = candidate
                        break
            if not table:
                continue
            date_col = 'trade_date' if table in {'prices', 'price_daily'} else 'date'
            rows = conn.execute(
                f'''
                select {date_col} as trade_date, close, volume
                from {table}
                where symbol = ?
                order by {date_col} asc, id asc
                ''',
                (symbol,),
            ).fetchall()
        except sqlite3.Error:
            conn.close()
            continue
        finally:
            conn.close()

        if not rows:
            continue
        deduped: dict[str, dict] = {}
        for row in rows:
            token = str(row['trade_date'] or '').strip()
            if not token:
                continue
            deduped[token] = {
                'date': token,
                'close': round(float(row['close'] or 0.0), 2),
                'volume': max(0, int(float(row['volume'] or 0.0))),
            }
        if deduped:
            return [deduped[key] for key in sorted(deduped)]
    return []


def read_company_snapshot(symbol: str) -> dict | None:
    layout = resolve_quantdb_layout()
    if not layout or not layout.main:
        return None
    conn = _connect(layout.main)
    if conn is None:
        return None

    code = f'A{to_kiwoom_symbol(symbol)}'
    try:
        run_id = _latest_run_id(conn, 'quantking_snapshot')
        params: list[object] = [code]
        where_sql = 'where code = ?'
        if run_id:
            where_sql += ' and run_id = ?'
            params.append(run_id)
        row = conn.execute(
            f'''
            select code, company, market, sector_large, sector_small,
                   price, mkt_cap, shares_outstanding, major_holder_ratio,
                   per, pbr, roe, roa, opm, dividend_yield, debt_ratio,
                   ev_ebitda, foreign_1m, return_1m, return_3m, f_score
            from quantking_snapshot
            {where_sql}
            order by id desc
            limit 1
            ''',
            tuple(params),
        ).fetchone()
    except sqlite3.Error:
        conn.close()
        return None
    finally:
        conn.close()

    if not row:
        return None

    def _float(key: str) -> float | None:
        v = row[key]
        return float(v) if v not in (None, '') else None

    return {
        'code': str(row['code'] or '').strip(),
        'name': str(row['company'] or symbol).strip() or symbol,
        'market': str(row['market'] or '').strip(),
        'sector_large': str(row['sector_large'] or '').strip(),
        'sector_small': str(row['sector_small'] or '').strip(),
        'price': _float('price'),
        'mkt_cap': _float('mkt_cap'),
        'shares_outstanding': _float('shares_outstanding'),
        'major_holder_ratio': _float('major_holder_ratio'),
        'per': _float('per'),
        'pbr': _float('pbr'),
        'roe': _float('roe'),
        'roa': _float('roa'),
        'opm': _float('opm'),
        'dividend_yield': _float('dividend_yield'),
        'debt_ratio': _float('debt_ratio'),
        'ev_ebitda': _float('ev_ebitda'),
        'foreign_1m': _float('foreign_1m'),
        'return_1m': _float('return_1m'),
        'return_3m': _float('return_3m'),
        'f_score': _float('f_score'),
    }


def read_eps_rows(symbol: str, as_of_date: str | None = None) -> list[dict]:
    layout = resolve_quantdb_layout()
    if not layout or not layout.snapshot:
        return []
    conn = _connect(layout.snapshot)
    if conn is None:
        return []

    code = f'A{to_kiwoom_symbol(symbol)}'
    cutoff = ''.join(ch for ch in str(as_of_date or '').strip() if ch.isdigit())
    try:
        rows = conn.execute(
            '''
            select code, metric, fiscal_year, fiscal_quarter, value
            from financials_quarterly
            where code = ? and metric = 'EPS'
            order by cast(fiscal_year as integer) asc, cast(replace(fiscal_quarter, 'Q', '') as integer) asc
            ''',
            (code,),
        ).fetchall()
    except sqlite3.Error:
        conn.close()
        return []
    finally:
        conn.close()

    values: list[tuple[str, float]] = []
    for row in rows:
        period = _quarter_period(str(row['fiscal_year'] or ''), str(row['fiscal_quarter'] or ''))
        value = row['value']
        if not period or value in (None, ''):
            continue
        values.append((period, float(value)))

    out: list[dict] = []
    for idx, (period, eps_value) in enumerate(values):
        available_token = _quarter_available_token(period[:4], period[4:])
        if cutoff and available_token and available_token > cutoff:
            continue
        yoy = None
        if idx >= 4:
            prev = values[idx - 4][1]
            if prev not in (0, None):
                yoy = ((eps_value / prev) - 1.0) * 100.0
        out.append(
            {
                'period': period,
                'available_date': available_token,
                'eps': round(eps_value, 2),
                'eps_yoy': round(float(yoy), 2) if yoy is not None else 0.0,
            }
        )
    return out
