"""Naver-sourced financial data reader — single source of truth.

All financial metrics (PER/EPS/ROE/revenue/etc.) come from data/sepa.db:
  - symbol_meta: current snapshot (from Naver integration API)
  - financials: annual + quarterly time series (from Naver finance API)

QuantDB is NOT used for financial metrics. It remains only for:
  - Universe listing (read_universe)
  - Supplementary metrics not in Naver (ROA, EV/EBITDA, f_score, foreign_1m)
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from sepa.data.symbols import to_kiwoom_symbol

DB_PATH = Path('data/sepa.db')

# Naver metric names → standard output keys
METRIC_MAP: dict[str, str] = {
    '매출액': 'revenue',
    '영업이익': 'op_profit',
    '당기순이익': 'net_income',
    '지배주주순이익': 'net_income',
    '비지배주주순이익': 'minority_income',
    '영업이익률': 'opm',
    '순이익률': 'npm',
    'ROE': 'roe',
    '부채비율': 'debt_ratio',
    '당좌비율': 'quick_ratio',
    '유보율': 'retention_ratio',
    'EPS': 'eps',
    'PER': 'per',
    'BPS': 'bps',
    'PBR': 'pbr',
    '주당배당금': 'dps',
}

OUTPUT_METRICS = [
    'revenue', 'op_profit', 'net_income', 'equity', 'total_debt',
    'opm', 'npm', 'roe', 'debt_ratio', 'eps', 'per', 'bps', 'pbr',
    'dps', 'dividend_yield',
]


def _connect() -> sqlite3.Connection | None:
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _bare(symbol: str) -> str:
    s = str(symbol or '').strip()
    for sfx in ('.KS', '.KQ', '.KN'):
        if s.upper().endswith(sfx):
            return s[:-len(sfx)]
    return s


# ---------------------------------------------------------------------------
# Snapshot (current values from symbol_meta)
# ---------------------------------------------------------------------------

def read_snapshot(symbol: str) -> dict | None:
    """Read current financial snapshot from symbol_meta (Naver-sourced)."""
    conn = _connect()
    if conn is None:
        return None
    code = _bare(symbol)
    try:
        row = conn.execute('SELECT * FROM symbol_meta WHERE symbol = ?', (code,)).fetchone()
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    if not row:
        return None
    d = dict(row)

    def _f(key: str) -> float | None:
        v = d.get(key)
        if v is None or v == '':
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    def _s(key: str) -> str:
        return str(d.get(key) or '').strip()

    return {
        'symbol': code,
        'name': _s('name'),
        'sector': _s('sector'),
        'industry': _s('industry'),
        'per': _f('per'),
        'eps': _f('eps'),
        'pbr': _f('pbr'),
        'bps': _f('bps'),
        'roe': _f('roe'),
        'revenue': _f('revenue'),
        'op_profit': _f('op_profit'),
        'net_income': _f('net_income'),
        'market_cap_display': _s('market_cap'),
        'market_cap_krw': _f('market_cap_krw'),
        'shares_outstanding': _f('shares_outstanding_calc'),
        'foreign_ratio': _s('foreign_ratio'),
        'dividend_yield': _parse_dividend_yield(_s('dividend_yield')),
        'description': _s('description'),
        'consensus_target': _s('consensus_target'),
        'consensus_opinion': _f('consensus_opinion'),
        'high_52w': _s('high_52w'),
        'low_52w': _s('low_52w'),
        # Source tracking
        'source': 'naver',
    }


def _parse_dividend_yield(raw: str) -> float | None:
    """Parse dividend_yield which may be '0.90%', 'N/A', or numeric."""
    if not raw or raw in ('N/A', '-', ''):
        return None
    try:
        return float(raw.rstrip('%'))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Price + Shares resolution (no QuantDB)
# ---------------------------------------------------------------------------

def resolve_price_shares(
    symbol: str,
    *,
    price_hint: float | None = None,
    shares_hint: float | None = None,
) -> tuple[float, float]:
    """Get price and shares from Naver data only.

    Priority:
      price: price_hint > OHLCV latest close
      shares: shares_hint > symbol_meta.shares_outstanding_calc
    """
    real_price = float(price_hint) if price_hint and price_hint > 0 else 0.0
    shares = float(shares_hint) if shares_hint and shares_hint > 0 else 0.0

    if real_price <= 0 or shares <= 0:
        conn = _connect()
        if conn:
            code = _bare(symbol)
            try:
                if real_price <= 0:
                    row = conn.execute(
                        'SELECT close FROM ohlcv WHERE symbol=? ORDER BY trade_date DESC LIMIT 1',
                        (code,),
                    ).fetchone()
                    if row:
                        real_price = float(row['close'])

                if shares <= 0:
                    row = conn.execute(
                        'SELECT shares_outstanding_calc FROM symbol_meta WHERE symbol=?',
                        (code,),
                    ).fetchone()
                    if row and row['shares_outstanding_calc']:
                        shares = float(row['shares_outstanding_calc'])
            except sqlite3.Error:
                pass
            finally:
                conn.close()

    return real_price, shares


# ---------------------------------------------------------------------------
# Derived metric computation
# ---------------------------------------------------------------------------

def derive_metrics(
    annual_data: dict[str, dict],
    quarter_data: dict[str, dict],
    real_price: float,
    snap_shares: float,
) -> None:
    """Compute NPM, OPM, ROE, debt_ratio, EPS, BPS, PER, PBR in-place."""
    for bucket in (annual_data, quarter_data):
        for _period, m in bucket.items():
            rev = m.get('revenue')
            ni = m.get('net_income')
            op = m.get('op_profit')
            equity = m.get('equity')
            debt = m.get('total_debt')
            if rev and ni and rev != 0 and 'npm' not in m:
                m['npm'] = round((ni / rev) * 100, 1)
            if rev and op and rev != 0 and 'opm' not in m:
                m['opm'] = round((op / rev) * 100, 1)
            if ni is not None and equity and equity > 0 and m.get('roe') is None:
                m['roe'] = round((ni / equity) * 100, 1)
            if debt is not None and equity and equity > 0 and m.get('debt_ratio') is None:
                m['debt_ratio'] = round((debt / equity) * 100, 1)
            if ni is not None and snap_shares > 0 and m.get('eps') is None:
                m['eps'] = int(round((ni * 100_000_000) / snap_shares))
            if equity is not None and snap_shares > 0 and m.get('bps') is None:
                m['bps'] = int(round((equity * 100_000_000) / snap_shares))
            eps_val = m.get('eps')
            if real_price > 0 and eps_val and eps_val > 0 and m.get('per') is None:
                m['per'] = round(real_price / eps_val, 1)
            bps_val = m.get('bps')
            if real_price > 0 and bps_val and bps_val > 0 and m.get('pbr') is None:
                m['pbr'] = round(real_price / bps_val, 1)


# ---------------------------------------------------------------------------
# Financial time series (from financials table)
# ---------------------------------------------------------------------------

def read_financial_series(
    symbol: str,
    *,
    price_hint: float | None = None,
    shares_hint: float | None = None,
) -> dict:
    """Read annual + quarterly financial data from Naver financials table.

    Returns: {annual: [...], quarterly: [...], metrics: [...]}
    """
    empty: dict = {'annual': [], 'quarterly': [], 'metrics': []}
    conn = _connect()
    if conn is None:
        return empty

    code = _bare(symbol)
    try:
        rows = conn.execute(
            'SELECT period, period_type, metric, value FROM financials WHERE symbol = ? ORDER BY period',
            (code,),
        ).fetchall()
    except sqlite3.Error:
        conn.close()
        return empty
    finally:
        conn.close()

    # Pivot into annual/quarterly buckets
    annual_data: dict[str, dict[str, float | None]] = {}
    quarter_data: dict[str, dict[str, float | None]] = {}

    for row in rows:
        period = str(row['period'])
        ptype = str(row['period_type'])
        metric_raw = str(row['metric'])
        val = float(row['value']) if row['value'] is not None else None

        key = METRIC_MAP.get(metric_raw)
        if not key:
            continue

        if ptype == 'quarterly' or 'Q' in period:
            quarter_data.setdefault(period, {})[key] = val
        else:
            annual_data.setdefault(period, {})[key] = val

    # If no financials rows, fall back to symbol_meta snapshot
    if not annual_data and not quarter_data:
        snap = read_snapshot(symbol)
        if snap:
            year = str(datetime.now().year)
            snap_metrics: dict[str, float | None] = {}
            for mk in ('per', 'eps', 'roe', 'pbr', 'bps', 'revenue', 'op_profit', 'net_income'):
                v = snap.get(mk)
                if v is not None:
                    snap_metrics[mk] = float(v)
            if snap_metrics:
                annual_data[year] = snap_metrics

        if not annual_data and not quarter_data:
            return empty

    # Derive metrics using Naver price/shares
    real_price, snap_shares = resolve_price_shares(symbol, price_hint=price_hint, shares_hint=shares_hint)
    derive_metrics(annual_data, quarter_data, real_price, snap_shares)

    # Sort and trim: last 4 years, last 8 quarters
    current_year = str(datetime.now().year)
    min_year = str(int(current_year) - 4)
    sorted_years = sorted(y for y in annual_data if y >= min_year)[-4:]
    if not sorted_years:
        sorted_years = sorted(annual_data)[-4:]
    min_quarter = f'{min_year}Q1'
    sorted_quarters = sorted(q for q in quarter_data if q >= min_quarter)[-8:]
    if not sorted_quarters:
        sorted_quarters = sorted(quarter_data)[-8:]

    int_metrics = {'revenue', 'op_profit', 'net_income', 'equity', 'total_debt', 'eps', 'bps', 'dps'}

    def _build_row(period: str, metrics: dict) -> dict:
        out: dict = {'period': period}
        for mk in OUTPUT_METRICS:
            v = metrics.get(mk)
            if v is None:
                out[mk] = None
            elif mk in int_metrics:
                out[mk] = int(round(v))
            else:
                out[mk] = round(v, 1)
        return out

    return {
        'annual': [_build_row(y, annual_data[y]) for y in sorted_years],
        'quarterly': [_build_row(q, quarter_data[q]) for q in sorted_quarters],
        'metrics': OUTPUT_METRICS,
    }


# ---------------------------------------------------------------------------
# Supplementary metrics from QuantDB (NOT financial data)
# ---------------------------------------------------------------------------

def read_supplementary(symbol: str) -> dict:
    """Read non-financial supplementary metrics from QuantDB.

    These are metrics Naver does not provide:
    ROA, EV/EBITDA, f_score, foreign_1m, return_1m, return_3m, etc.
    """
    try:
        from sepa.data.quantdb import read_company_snapshot
        snap = read_company_snapshot(symbol)
    except Exception:
        snap = None
    if not snap:
        return {}
    return {
        'roa': snap.get('roa'),
        'opm_quantdb': snap.get('opm'),
        'ev_ebitda': snap.get('ev_ebitda'),
        'foreign_1m': snap.get('foreign_1m'),
        'return_1m': snap.get('return_1m'),
        'return_3m': snap.get('return_3m'),
        'f_score': snap.get('f_score'),
        'major_holder_ratio': snap.get('major_holder_ratio'),
        'source': 'quantdb',
    }
