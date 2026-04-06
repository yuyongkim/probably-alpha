"""EPS series reader — Naver only (no QuantDB).

Two sources:
1. _read_naver_eps() — direct EPS from financial.db financials table
2. _read_naver_ni_eps() — computed EPS from net_income / shares

Fallback: snapshot PER reverse-calc for stocks with no financials.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from sepa.data.price_history import normalize_date_token

EPS_PATH = Path('data/market-data/fundamentals/eps.csv')
_DB_PATH = Path('data/financial.db')
_META_DB = Path('data/meta.db')


def _strip_suffix(symbol: str) -> str:
    s = symbol.upper().strip()
    for suffix in ('.KS', '.KQ'):
        if s.endswith(suffix):
            return s[:-len(suffix)]
    return s


def _period_available_token(period: str) -> str:
    raw = str(period or '').strip().upper()
    if len(raw) == 4 and raw.isdigit():
        year = int(raw)
        return date(year + 1, 3, 15).strftime('%Y%m%d')
    if len(raw) != 6 or not raw[:4].isdigit() or not raw.endswith(('Q1', 'Q2', 'Q3', 'Q4')):
        return ''
    year = int(raw[:4])
    quarter = raw[-2:]
    mapping = {
        'Q1': (date(year, 3, 31), 45),
        'Q2': (date(year, 6, 30), 45),
        'Q3': (date(year, 9, 30), 45),
        'Q4': (date(year, 12, 31), 75),
    }
    quarter_end, lag_days = mapping[quarter]
    return (quarter_end + timedelta(days=lag_days)).strftime('%Y%m%d')


# ---------------------------------------------------------------------------
# Source 1: Direct EPS from financials table
# ---------------------------------------------------------------------------

def _read_naver_eps(symbol: str, cutoff: str) -> list[dict]:
    if not _DB_PATH.exists():
        return []
    sym = _strip_suffix(symbol)
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT period, period_type, value FROM financials "
            "WHERE symbol = ? AND metric = 'EPS' ORDER BY period",
            (sym,),
        ).fetchall()
        conn.close()
    except sqlite3.Error:
        return []

    out: list[dict] = []
    for r in rows:
        period = str(r['period'] or '').strip()
        ptype = str(r['period_type'] or '').strip()
        if not period:
            continue
        available_token = _period_available_token(period)
        if cutoff and available_token and available_token > cutoff:
            continue
        out.append({
            'period': period,
            'period_type': 'annual' if ptype == 'annual' or (len(period) == 4 and 'Q' not in period) else 'quarterly',
            'available_date': available_token,
            'eps': float(r['value']) if r['value'] is not None else 0.0,
        })
    return out


# ---------------------------------------------------------------------------
# Source 2: EPS from net_income / shares
# ---------------------------------------------------------------------------

def _read_naver_ni_eps(symbol: str, cutoff: str) -> list[dict]:
    if not _DB_PATH.exists():
        return []
    sym = _strip_suffix(symbol)
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.row_factory = sqlite3.Row
        ni_rows = conn.execute(
            "SELECT period, period_type, value FROM financials "
            "WHERE symbol = ? AND metric IN ('당기순이익', '순이익') ORDER BY period",
            (sym,),
        ).fetchall()
        conn.close()
    except sqlite3.Error:
        return []

    if not ni_rows:
        return []

    shares = _get_shares(sym)
    if not shares or shares <= 0:
        return []

    out: list[dict] = []
    for r in ni_rows:
        period = str(r['period'] or '').strip()
        ptype = str(r['period_type'] or '').strip()
        if not period:
            continue
        available_token = _period_available_token(period)
        if cutoff and available_token and available_token > cutoff:
            continue
        ni = float(r['value']) if r['value'] is not None else 0.0
        eps = round((ni * 100_000_000) / shares)
        out.append({
            'period': period,
            'period_type': 'annual' if ptype == 'annual' or (len(period) == 4 and 'Q' not in period) else 'quarterly',
            'available_date': available_token,
            'eps': float(eps),
        })
    return out


def _get_shares(symbol: str) -> float | None:
    if not _META_DB.exists():
        return None
    try:
        conn = sqlite3.connect(str(_META_DB))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            'SELECT shares_outstanding_calc FROM symbol_meta WHERE symbol = ?',
            (_strip_suffix(symbol),),
        ).fetchone()
        conn.close()
        if row and row['shares_outstanding_calc']:
            return float(row['shares_outstanding_calc'])
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Fallback: snapshot PER reverse-calc
# ---------------------------------------------------------------------------

def _read_quantdb_long_eps(symbol: str, cutoff: str) -> list[dict]:
    """Read long EPS history from QuantDB (2009~2018) + Live NI (2016~2025)."""
    out: list[dict] = []
    sym = _strip_suffix(symbol)

    try:
        from sepa.data.quantdb_layout import resolve_quantdb_layout
        from sepa.data.symbols import to_kiwoom_symbol
        layout = resolve_quantdb_layout()
        if not layout or not layout.snapshot:
            return []

        code = f'A{to_kiwoom_symbol(sym)}'

        # 1) QuantDB financials_quarterly EPS (2009~2018)
        import sqlite3
        conn = sqlite3.connect(str(layout.snapshot), timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT fiscal_year, fiscal_quarter, value FROM financials_quarterly "
                "WHERE code = ? AND metric = 'EPS' ORDER BY fiscal_year, fiscal_quarter",
                (code,),
            ).fetchall()
        except sqlite3.Error:
            rows = []
        finally:
            conn.close()

        for r in rows:
            y = str(r['fiscal_year'] or '').strip()
            q = str(r['fiscal_quarter'] or '').strip().upper()
            if not y.isdigit() or q not in ('Q1', 'Q2', 'Q3', 'Q4'):
                continue
            period = f'{y}{q}'
            avail = _period_available_token(period)
            if cutoff and avail and avail > cutoff:
                continue
            out.append({
                'period': period, 'period_type': 'quarterly',
                'available_date': avail, 'eps': float(r['value']),
            })

        # 2) Live financials NI → EPS (2016~2025)
        live_db = layout.snapshot.parent / 'stock_live_financials.db' if layout.snapshot else None
        if live_db and live_db.exists():
            shares = _get_shares(sym)
            if shares and shares > 0:
                lconn = sqlite3.connect(str(live_db), timeout=10)
                lconn.row_factory = sqlite3.Row
                try:
                    # Annual
                    for r in lconn.execute(
                        "SELECT fiscal_year, value FROM stock_live_financials_annual "
                        "WHERE code = ? AND metric IN ('당기순이익','순이익') ORDER BY fiscal_year",
                        (code,),
                    ).fetchall():
                        y = str(r['fiscal_year'] or '').strip()
                        if not y.isdigit():
                            continue
                        avail = _period_available_token(y)
                        if cutoff and avail and avail > cutoff:
                            continue
                        ni = float(r['value'] or 0)
                        out.append({
                            'period': y, 'period_type': 'annual',
                            'available_date': avail,
                            'eps': float(round((ni * 100_000_000) / shares)),
                        })

                    # Quarterly
                    for r in lconn.execute(
                        "SELECT fiscal_year, fiscal_quarter, value FROM stock_live_financials_quarterly "
                        "WHERE code = ? AND metric IN ('당기순이익','순이익') ORDER BY fiscal_year, fiscal_quarter",
                        (code,),
                    ).fetchall():
                        y = str(r['fiscal_year'] or '').strip()
                        q = str(r['fiscal_quarter'] or '').strip().upper()
                        if not y.isdigit() or q not in ('Q1', 'Q2', 'Q3', 'Q4'):
                            continue
                        period = f'{y}{q}'
                        avail = _period_available_token(period)
                        if cutoff and avail and avail > cutoff:
                            continue
                        ni = float(r['value'] or 0)
                        out.append({
                            'period': period, 'period_type': 'quarterly',
                            'available_date': avail,
                            'eps': float(round((ni * 100_000_000) / shares)),
                        })
                except sqlite3.Error:
                    pass
                finally:
                    lconn.close()

    except Exception:
        pass

    return out


def _snapshot_eps_fallback(symbol: str) -> list[dict]:
    try:
        from sepa.data.naver_financials import read_snapshot
        snap = read_snapshot(symbol)
        if snap:
            per = snap.get('per')
            # Get latest price from OHLCV
            from sepa.data.ohlcv_db import read_ohlcv
            rows = read_ohlcv(symbol)
            price = rows[-1]['close'] if rows else 0
            if per and per != 0 and price > 0:
                from datetime import datetime
                return [{
                    'period': str(datetime.now().year),
                    'period_type': 'annual',
                    'available_date': '',
                    'eps': round(price / per, 2),
                }]
    except Exception:
        pass
    return []


# ---------------------------------------------------------------------------
# YoY computation
# ---------------------------------------------------------------------------

def _compute_yoy(rows: list[dict]) -> list[dict]:
    by_period: dict[str, dict] = {r['period']: r for r in rows}
    for row in rows:
        period = row['period']
        ptype = row.get('period_type', '')
        prev_period = None
        if ptype == 'annual' and len(period) == 4 and period.isdigit():
            prev_period = str(int(period) - 1)
        elif ptype == 'quarterly' and len(period) == 6 and period[4] == 'Q':
            year = int(period[:4])
            q = period[5]
            prev_period = f'{year - 1}Q{q}'

        prev = by_period.get(prev_period) if prev_period else None
        if prev and abs(prev['eps']) > 0.001:
            row['eps_yoy'] = round(((row['eps'] - prev['eps']) / abs(prev['eps'])) * 100.0, 2)
        else:
            row['eps_yoy'] = 0.0
    return rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_eps_series(
    symbol: str,
    path: Path = EPS_PATH,
    as_of_date: str | None = None,
) -> list[dict]:
    return [
        {
            'period': row[0],
            'period_type': row[1],
            'available_date': row[2],
            'eps': row[3],
            'eps_yoy': row[4],
        }
        for row in _read_eps_series_cached(
            symbol.upper(),
            normalize_date_token(as_of_date),
            _db_mtime_ns(),
        )
    ]


def _db_mtime_ns() -> int:
    try:
        return _DB_PATH.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


@lru_cache(maxsize=512)
def _read_eps_series_cached(
    symbol: str,
    cutoff: str,
    db_mtime_ns: int,
) -> tuple[tuple[str, str, str, float, float], ...]:
    # Source 1 (long history): QuantDB EPS + Live NI → EPS
    quantdb_rows = _read_quantdb_long_eps(symbol, cutoff)

    # Source 2: Naver direct EPS (most recent, highest priority)
    naver_rows = _read_naver_eps(symbol, cutoff)

    # Source 3: Naver net_income → EPS
    naver_ni_rows = _read_naver_ni_eps(symbol, cutoff)

    # Merge: QuantDB (oldest) < NI-derived < Naver direct (newest, highest priority)
    by_period: dict[str, dict] = {}
    for row in quantdb_rows:
        by_period[row['period']] = row
    for row in naver_ni_rows:
        by_period[row['period']] = row
    for row in naver_rows:
        by_period[row['period']] = row

    # Fallback: snapshot PER reverse-calc if nothing found
    if not by_period:
        for row in _snapshot_eps_fallback(symbol):
            by_period[row['period']] = row

    sorted_rows = sorted(by_period.values(), key=lambda r: r['period'])
    sorted_rows = _compute_yoy(sorted_rows)

    return tuple(
        (row['period'], row.get('period_type', 'quarterly'), row.get('available_date', ''), row['eps'], row.get('eps_yoy', 0.0))
        for row in sorted_rows
    )


def eps_growth_snapshot(symbol: str, as_of_date: str | None = None) -> dict:
    series = read_eps_series(symbol, as_of_date=as_of_date)
    if not series:
        return {'status': 'missing', 'latest_yoy': 0.0, 'acceleration': 0.0, 'growth_hint': 0.5}

    yoy_values = [row.get('eps_yoy', 0.0) for row in series]
    latest_yoy = float(yoy_values[-1]) if yoy_values else 0.0
    acceleration = latest_yoy - float(yoy_values[-2]) if len(yoy_values) >= 2 else 0.0

    if latest_yoy >= 25 and acceleration >= 0:
        status, growth_hint = 'explosive', 2.0
    elif latest_yoy >= 15:
        status, growth_hint = 'strong', 1.5
    elif latest_yoy > 0:
        status, growth_hint = 'improving', 1.0
    else:
        status, growth_hint = 'weak', 0.5

    return {
        'status': status,
        'latest_yoy': round(latest_yoy, 2),
        'acceleration': round(acceleration, 2),
        'growth_hint': growth_hint,
    }
