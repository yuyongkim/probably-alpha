from __future__ import annotations

import csv
import os
import sqlite3
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from sepa.data.price_history import normalize_date_token
from sepa.data.quantdb import health as quantdb_health
from sepa.data.quantdb import read_eps_rows as read_quantdb_eps_rows

EPS_PATH = Path('data/market-data/fundamentals/eps.csv')
_DB_PATH = Path('data/financial.db')


def _to_num(value) -> float:
    try:
        return float(str(value).replace(',', ''))
    except Exception:
        return 0.0


def _strip_suffix(symbol: str) -> str:
    """'005930.KS' -> '005930'"""
    s = symbol.upper().strip()
    for suffix in ('.KS', '.KQ'):
        if s.endswith(suffix):
            return s[:-len(suffix)]
    return s


def _period_available_token(period: str) -> str:
    raw = str(period or '').strip().upper()
    # Annual period: e.g. '2024'
    if len(raw) == 4 and raw.isdigit():
        year = int(raw)
        # Annual reports available ~75 days after fiscal year end
        available = date(year + 1, 3, 15)
        return available.strftime('%Y%m%d')
    # Quarterly period: e.g. '2024Q3'
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
    available_date = quarter_end + timedelta(days=lag_days)
    return available_date.strftime('%Y%m%d')


# ---------------------------------------------------------------------------
# EPS data sources (priority order)
# ---------------------------------------------------------------------------

def _read_naver_eps(symbol: str, cutoff: str) -> list[dict]:
    """Read EPS from ohlcv.db financials table (Naver-sourced).
    Returns both annual and quarterly rows."""
    if not _DB_PATH.exists():
        return []
    sym = _strip_suffix(symbol.upper().strip())
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT period, period_type, value FROM financials "
            "WHERE symbol = ? AND metric = 'EPS' "
            "ORDER BY period",
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


def _read_naver_ni_eps(symbol: str, cutoff: str) -> list[dict]:
    """Compute EPS from 당기순이익 in ohlcv.db financials when direct EPS is missing."""
    if not _DB_PATH.exists():
        return []
    sym = _strip_suffix(symbol.upper().strip())
    try:
        conn = sqlite3.connect(str(_DB_PATH))
        conn.row_factory = sqlite3.Row
        ni_rows = conn.execute(
            "SELECT period, period_type, value FROM financials "
            "WHERE symbol = ? AND metric = '당기순이익' "
            "ORDER BY period",
            (sym,),
        ).fetchall()
        conn.close()
    except sqlite3.Error:
        return []

    if not ni_rows:
        return []

    # Get shares for EPS calculation
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
        # 당기순이익 is in 억원; EPS = ni * 1억 / shares
        eps = round((ni * 100_000_000) / shares)
        out.append({
            'period': period,
            'period_type': 'annual' if ptype == 'annual' or (len(period) == 4 and 'Q' not in period) else 'quarterly',
            'available_date': available_token,
            'eps': float(eps),
        })
    return out


def _read_quantdb_eps(symbol: str, cutoff: str) -> list[dict]:
    """Read EPS from QuantDB financials_quarterly + stock_live_financials."""
    from sepa.data.quantdb_layout import resolve_quantdb_layout, _table_exists
    from sepa.data.symbols import to_kiwoom_symbol

    layout = resolve_quantdb_layout()
    if not layout or not layout.snapshot:
        return []

    code = f'A{to_kiwoom_symbol(symbol)}'
    out: list[dict] = []

    # 1) financials_quarterly (metric='EPS')
    try:
        conn = sqlite3.connect(str(layout.snapshot))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT fiscal_year, fiscal_quarter, value FROM financials_quarterly "
            "WHERE code = ? AND metric = 'EPS' "
            "ORDER BY fiscal_year, fiscal_quarter",
            (code,),
        ).fetchall()
        conn.close()
    except sqlite3.Error:
        rows = []

    for r in rows:
        y = str(r['fiscal_year'] or '').strip()
        q = str(r['fiscal_quarter'] or '').strip().upper()
        if not y.isdigit() or q not in ('Q1', 'Q2', 'Q3', 'Q4'):
            continue
        period = f'{y}{q}'
        available_token = _period_available_token(period)
        if cutoff and available_token and available_token > cutoff:
            continue
        out.append({
            'period': period,
            'period_type': 'quarterly',
            'available_date': available_token,
            'eps': float(r['value']) if r['value'] is not None else 0.0,
        })

    # 2) stock_live_financials — compute EPS from 당기순이익
    live_db = layout.snapshot.parent / 'stock_live_financials.db' if layout.snapshot else None
    if live_db and live_db.exists():
        shares = _get_shares(_strip_suffix(symbol))
        if shares and shares > 0:
            try:
                lconn = sqlite3.connect(str(live_db))
                lconn.row_factory = sqlite3.Row

                # Annual — try both '당기순이익' and '순이익' (live DB uses shorter name)
                try:
                    annual_rows = lconn.execute(
                        "SELECT fiscal_year, value FROM stock_live_financials_annual "
                        "WHERE code = ? AND metric IN ('당기순이익','순이익') ORDER BY fiscal_year",
                        (code,),
                    ).fetchall()
                except sqlite3.Error:
                    annual_rows = []

                for r in annual_rows:
                    y = str(r['fiscal_year'] or '').strip()
                    if not y.isdigit():
                        continue
                    period = y
                    available_token = _period_available_token(period)
                    if cutoff and available_token and available_token > cutoff:
                        continue
                    ni = float(r['value']) if r['value'] is not None else 0.0
                    eps = round((ni * 100_000_000) / shares)
                    out.append({
                        'period': period,
                        'period_type': 'annual',
                        'available_date': available_token,
                        'eps': float(eps),
                    })

                # Quarterly — try both '당기순이익' and '순이익'
                try:
                    qtr_rows = lconn.execute(
                        "SELECT fiscal_year, fiscal_quarter, value FROM stock_live_financials_quarterly "
                        "WHERE code = ? AND metric IN ('당기순이익','순이익') ORDER BY fiscal_year, fiscal_quarter",
                        (code,),
                    ).fetchall()
                except sqlite3.Error:
                    qtr_rows = []

                for r in qtr_rows:
                    y = str(r['fiscal_year'] or '').strip()
                    q = str(r['fiscal_quarter'] or '').strip().upper()
                    if not y.isdigit() or q not in ('Q1', 'Q2', 'Q3', 'Q4'):
                        continue
                    period = f'{y}{q}'
                    available_token = _period_available_token(period)
                    if cutoff and available_token and available_token > cutoff:
                        continue
                    ni = float(r['value']) if r['value'] is not None else 0.0
                    eps = round((ni * 100_000_000) / shares)
                    out.append({
                        'period': period,
                        'period_type': 'quarterly',
                        'available_date': available_token,
                        'eps': float(eps),
                    })

                lconn.close()
            except sqlite3.Error:
                pass

    return out


def _get_shares(symbol: str) -> float | None:
    """Get shares outstanding for EPS computation."""
    sym = _strip_suffix(symbol)
    try:
        from sepa.data.quantdb import read_company_snapshot
        snap = read_company_snapshot(sym)
        if snap:
            raw = float(snap.get('shares_outstanding') or 0)
            if raw > 0:
                return raw
            mkt_cap = float(snap.get('mkt_cap') or 0)
            price = float(snap.get('price') or 0)
            if mkt_cap > 0 and price > 0:
                return (mkt_cap * 100_000_000) / price
    except Exception:
        pass
    return None


def _read_financial_summary_eps(symbol: str, cutoff: str) -> list[dict]:
    """Extract EPS from read_financial_summary() + snapshot PER fallback.

    Covers ~2800 stocks because financial_summary computes EPS from
    net_income/shares. For the remaining ~400 that have no financials
    but DO have snapshot PER+price, we reverse-compute EPS = price / PER.
    """
    out: list[dict] = []

    # 1) Full financial_summary (gives time series with computed EPS)
    try:
        from sepa.data.quantdb import read_financial_summary
        fs = read_financial_summary(symbol)
    except Exception:
        fs = {'annual': [], 'quarterly': []}

    for ptype, key in [('annual', 'annual'), ('quarterly', 'quarterly')]:
        for row in fs.get(key, []):
            eps = row.get('eps')
            if eps is None:
                continue
            period = str(row.get('period', ''))
            available_token = _period_available_token(period)
            if cutoff and available_token and available_token > cutoff:
                continue
            out.append({
                'period': period,
                'period_type': ptype,
                'available_date': available_token,
                'eps': float(eps),
            })

    # 2) If no time-series EPS, reverse-calc from snapshot PER (fast, ~2400 stocks)
    if not out:
        try:
            from sepa.data.quantdb import read_company_snapshot
            snap = read_company_snapshot(symbol)
            if snap:
                per = float(snap.get('per') or 0)
                price = float(snap.get('price') or 0)
                if per != 0 and price > 0:
                    from datetime import datetime
                    out.append({
                        'period': str(datetime.now().year),
                        'period_type': 'annual',
                        'available_date': '',
                        'eps': round(price / per, 2),
                    })
        except Exception:
            pass

    return out


# ---------------------------------------------------------------------------
# YoY computation
# ---------------------------------------------------------------------------

def _compute_yoy(rows: list[dict]) -> list[dict]:
    """Compute YoY growth for sorted EPS rows.

    Annual: compare year N vs year N-1.
    Quarterly: compare quarter vs same quarter year-ago.
    """
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
# Main public API
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
            str(path),
            _path_mtime_ns(path),
            normalize_date_token(as_of_date),
            str(os.getenv('SEPA_EPS_SOURCE', 'auto') or 'auto').strip().lower(),
            bool(quantdb_health().get('has_financials_quarterly')),
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
    path_str: str,
    path_mtime_ns: int,
    cutoff: str,
    source_raw: str,
    quantdb_ready: bool,
    db_mtime_ns: int,
) -> tuple[tuple[str, str, str, float, float], ...]:
    # Priority 1: Naver direct EPS (ohlcv.db financials)
    naver_rows = _read_naver_eps(symbol, cutoff)

    # Priority 2: Naver 당기순이익 → EPS (ohlcv.db financials)
    naver_ni_rows = _read_naver_ni_eps(symbol, cutoff)

    # Priority 3: QuantDB EPS + live 당기순이익 → EPS
    quantdb_rows = _read_quantdb_eps(symbol, cutoff)

    # Priority 4: financial_summary fallback (covers ~2800 stocks via QuantDB)
    fs_rows = _read_financial_summary_eps(symbol, cutoff)

    # Merge: deduplicate by period, prefer Naver > Naver NI > QuantDB > fin_summary
    by_period: dict[str, dict] = {}
    for row in fs_rows:
        by_period[row['period']] = row
    for row in quantdb_rows:
        by_period[row['period']] = row
    for row in naver_ni_rows:
        by_period[row['period']] = row
    for row in naver_rows:
        by_period[row['period']] = row

    sorted_rows = sorted(by_period.values(), key=lambda r: r['period'])
    sorted_rows = _compute_yoy(sorted_rows)

    return tuple(
        (row['period'], row.get('period_type', 'quarterly'), row.get('available_date', ''), row['eps'], row.get('eps_yoy', 0.0))
        for row in sorted_rows
    )


def _path_mtime_ns(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


def eps_growth_snapshot(symbol: str, as_of_date: str | None = None) -> dict:
    series = read_eps_series(symbol, as_of_date=as_of_date)
    if not series:
        return {
            'status': 'missing',
            'latest_yoy': 0.0,
            'acceleration': 0.0,
            'growth_hint': 0.5,
        }

    yoy_values = [row.get('eps_yoy', 0.0) for row in series]
    latest_yoy = float(yoy_values[-1]) if yoy_values else 0.0
    acceleration = latest_yoy - float(yoy_values[-2]) if len(yoy_values) >= 2 else 0.0

    if latest_yoy >= 25 and acceleration >= 0:
        status = 'explosive'
        growth_hint = 2.0
    elif latest_yoy >= 15:
        status = 'strong'
        growth_hint = 1.5
    elif latest_yoy > 0:
        status = 'improving'
        growth_hint = 1.0
    else:
        status = 'weak'
        growth_hint = 0.5

    return {
        'status': status,
        'latest_yoy': round(latest_yoy, 2),
        'acceleration': round(acceleration, 2),
        'growth_hint': growth_hint,
    }
