from __future__ import annotations

import sqlite3

from sepa.data.quantdb_layout import (
    QuantDbLayout,
    _table_exists,
    resolve_quantdb_layout,
)
from sepa.data.symbols import to_kiwoom_symbol


def _connect(path) -> sqlite3.Connection | None:
    """Open a read-only connection with Row factory, or return None."""
    from pathlib import Path

    if not path or not Path(path).exists() or not Path(path).is_file() or Path(path).stat().st_size <= 0:
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


# Metric name -> output key mapping.
# Korean metric names are stored as-is in the DB.
METRIC_MAP: dict[str, str] = {
    '매출': 'revenue',
    '매출액': 'revenue',
    '연간매출': 'revenue',
    '영익': 'op_profit',
    '영업이익': 'op_profit',
    '연간영익': 'op_profit',
    '순익': 'net_income',
    '순이익': 'net_income',
    '연간순익': 'net_income',
    '지배순익': 'net_income',
    '자본총계': 'equity',
    '부채총계': 'total_debt',
    'EPS': 'eps',
    'BPS': 'bps',
    'PER': 'per',
    'PBR': 'pbr',
    'ROE': 'roe',
    'ROA': 'roa',
    '부채비율': 'debt_ratio',
    'DPS': 'dps',
    '시가배당율': 'dividend_yield',
    'OPM(연결)': 'opm',
    'OPM(누적)': 'opm',
    '순익율(연결)': 'npm',
}

OUTPUT_METRICS = [
    'revenue', 'op_profit', 'net_income', 'equity', 'total_debt',
    'opm', 'npm', 'roe', 'debt_ratio', 'eps', 'per', 'bps', 'pbr',
    'dps', 'dividend_yield',
]

RELATIVE_OFFSETS = {
    '이번분기': 0,
    '전분기': -1,
    '전전분기': -2,
    '전전전분기': -3,
    '다음분기': 1,
}


def _match_metric(raw_metric: str) -> str | None:
    m = str(raw_metric or '').strip()
    if m in METRIC_MAP:
        return METRIC_MAP[m]
    return None


def _offset_quarter(y: int, q: int, offset: int) -> tuple[int, int]:
    total = (y * 4 + q - 1) + offset
    return (total // 4, total % 4 + 1)


def read_financial_summary(symbol: str) -> dict:
    """Return last 4 years of annual data and last 6 quarters for key financial metrics.

    Connects to the ``layout.snapshot`` DB (``financials_quarterly`` table) and
    pivots the long-form (code, metric, fiscal_year, fiscal_quarter, value) rows
    into a compact structure suitable for a Naver-Finance-style performance table.
    """
    empty: dict = {'annual': [], 'quarterly': [], 'metrics': []}
    layout = resolve_quantdb_layout()
    if not layout or not layout.snapshot:
        return empty
    conn = _connect(layout.snapshot)
    if conn is None:
        return empty

    code = f'A{to_kiwoom_symbol(symbol)}'

    try:
        rows = conn.execute(
            '''
            select metric, fiscal_year, fiscal_quarter, value
            from financials_quarterly
            where code = ?
            ''',
            (code,),
        ).fetchall()
    except sqlite3.Error:
        conn.close()
        return empty
    finally:
        conn.close()

    # --- Merge live financials from stock_live_financials.db (if available) ---
    live_db = layout.snapshot.parent / 'stock_live_financials.db' if layout.snapshot else None
    if live_db and live_db.exists():
        live_conn = _connect(live_db)
        if live_conn is not None:
            try:
                live_annual = live_conn.execute(
                    'select metric, fiscal_year, value from stock_live_financials_annual where code = ?',
                    (code,),
                ).fetchall()
                live_quarterly = live_conn.execute(
                    'select metric, fiscal_year, fiscal_quarter, value from stock_live_financials_quarterly where code = ?',
                    (code,),
                ).fetchall()
                # Convert to same format as financials_quarterly rows
                for r in live_annual:
                    rows.append({'metric': r[0], 'fiscal_year': str(r[1]), 'fiscal_quarter': '', 'value': r[2]})
                for r in live_quarterly:
                    rows.append({'metric': r[0], 'fiscal_year': str(r[1]), 'fiscal_quarter': str(r[2] or ''), 'value': r[3]})
            except sqlite3.Error:
                pass
            finally:
                live_conn.close()

    if not rows:
        return empty

    # --- Resolve relative quarters to absolute (e.g. '이번분기' -> '2026Q1') ---
    # Determine base date from the quantking_snapshot run_id
    def _resolve_base_quarter() -> tuple[int, int]:
        """Return (year, quarter_num) for '이번분기' based on the snapshot run date."""
        try:
            main_conn = _connect(layout.main) if layout and layout.main else None
            if main_conn is None:
                return (2026, 1)
            rid = _latest_run_id(main_conn, 'quantking_snapshot')
            main_conn.close()
            if rid and len(rid) >= 8:
                y, m = int(rid[:4]), int(rid[4:6])
                q = (m - 1) // 3 + 1
                return (y, q)
        except (sqlite3.Error, ValueError, TypeError, OSError):
            pass
        return (2026, 1)

    base_y, base_q = _resolve_base_quarter()

    # Build a resolved map: actual_metric_name_in_db -> output_key
    # Must be done AFTER live DB merge so all metric names are captured.
    distinct_metrics: set[str] = {str(r['metric'] or '').strip() for r in rows}
    resolved_map: dict[str, str] = {}
    for dm in distinct_metrics:
        matched = _match_metric(dm)
        if matched:
            resolved_map[dm] = matched

    # Bucket data: (fiscal_year, fiscal_quarter) -> {metric_key: value}
    annual_data: dict[str, dict[str, float | None]] = {}   # year -> metrics
    quarter_data: dict[str, dict[str, float | None]] = {}   # 'YYYYQn' -> metrics

    for row in rows:
        metric_raw = str(row['metric'] or '').strip()
        key = resolved_map.get(metric_raw)
        if not key:
            continue
        year = str(row['fiscal_year'] or '').strip()
        quarter = str(row['fiscal_quarter'] or '').strip()
        val_raw = row['value']
        val = float(val_raw) if val_raw not in (None, '') else None

        # Handle relative periods (이번분기, 전분기, etc.)
        if year == 'relative':
            offset = RELATIVE_OFFSETS.get(quarter)
            if offset is None:
                continue
            abs_y, abs_q = _offset_quarter(base_y, base_q, offset)
            period_key = f'{abs_y}Q{abs_q}'
            quarter_data.setdefault(period_key, {})[key] = val
            continue

        if not year or not year.isdigit():
            continue

        quarter_upper = quarter.upper()
        if quarter_upper in ('Q1', 'Q2', 'Q3', 'Q4'):
            period_key = f'{year}{quarter_upper}'
            quarter_data.setdefault(period_key, {})[key] = val
        else:
            annual_data.setdefault(year, {})[key] = val

    # Infer annual data from quarterly data for years that have all 4 quarters.
    # This covers years where only quarterly data exists (e.g. 2019-2025).
    if quarter_data:
        flow_metrics = {'revenue', 'op_profit', 'net_income'}
        years_in_quarters: dict[str, list[str]] = {}
        for qk in quarter_data:
            y = qk[:4]
            years_in_quarters.setdefault(y, []).append(qk)
        for y, qkeys in years_in_quarters.items():
            if len(qkeys) < 4:
                continue
            agg: dict[str, float | None] = {}
            for qk in sorted(qkeys):
                qd = quarter_data[qk]
                for mk in OUTPUT_METRICS:
                    if mk in flow_metrics:
                        if qd.get(mk) is not None:
                            agg[mk] = (agg.get(mk) or 0) + qd[mk]  # type: ignore[operator]
                    else:
                        # For snapshot metrics, take the last quarter value
                        if qd.get(mk) is not None:
                            agg[mk] = qd[mk]
            if y not in annual_data:
                annual_data[y] = agg

    # Compute NPM (net profit margin) from net_income / revenue if not present
    for bucket in (annual_data, quarter_data):
        for period, metrics in bucket.items():
            rev = metrics.get('revenue')
            ni = metrics.get('net_income')
            if rev and ni and rev != 0 and 'npm' not in metrics:
                metrics['npm'] = round((ni / rev) * 100, 2)
            # Compute OPM from op_profit / revenue if not present
            op = metrics.get('op_profit')
            if rev and op and rev != 0 and 'opm' not in metrics:
                metrics['opm'] = round((op / rev) * 100, 2)

    # --- Derive valuation metrics from fundamentals ---
    # Use real OHLCV price (not stale snapshot price which may be pre-split).
    # Shares estimated from mkt_cap(억원) and real price.
    from sepa.data.price_history import read_price_series as _read_price

    # Import read_company_snapshot locally to avoid circular imports
    from sepa.data.quantdb import read_company_snapshot

    snap = read_company_snapshot(symbol)
    snap_mkt_cap = float(snap.get('mkt_cap') or 0) if snap else 0  # 억원
    _ohlcv = _read_price(symbol)
    real_price = float(_ohlcv[-1].get('close', 0)) if _ohlcv else 0
    if real_price <= 0 and snap:
        real_price = float(snap.get('price') or 0)
    # shares = mkt_cap(억원) * 1억 / real_price
    snap_shares = (snap_mkt_cap * 100_000_000 / real_price) if real_price > 0 and snap_mkt_cap > 0 else 0

    for bucket in (annual_data, quarter_data):
        for period, m in bucket.items():
            equity = m.get('equity')
            debt = m.get('total_debt')
            ni = m.get('net_income')
            # ROE = net_income / equity * 100 (both in 억원)
            if ni is not None and equity and equity > 0 and m.get('roe') is None:
                m['roe'] = round((ni / equity) * 100, 2)
            # 부채비율 = total_debt / equity * 100
            if debt is not None and equity and equity > 0 and m.get('debt_ratio') is None:
                m['debt_ratio'] = round((debt / equity) * 100, 2)
            # EPS = net_income(억원) * 1억 / shares
            if ni is not None and snap_shares > 0 and m.get('eps') is None:
                m['eps'] = round((ni * 100_000_000) / snap_shares, 0)
            # BPS = equity(억원) * 1억 / shares
            if equity is not None and snap_shares > 0 and m.get('bps') is None:
                m['bps'] = round((equity * 100_000_000) / snap_shares, 0)
            # PER = real_price / EPS
            eps_val = m.get('eps')
            if real_price > 0 and eps_val and eps_val > 0 and m.get('per') is None:
                m['per'] = round(real_price / eps_val, 2)
            # PBR = real_price / BPS
            bps_val = m.get('bps')
            if real_price > 0 and bps_val and bps_val > 0 and m.get('pbr') is None:
                m['pbr'] = round(real_price / bps_val, 2)
            # DPS placeholder (would need dividend data)
            # dividend_yield placeholder (would need DPS)

    # Sort and trim: most recent 4 years (2022+), most recent 8 quarters
    from datetime import datetime
    current_year = str(datetime.now().year)
    min_year = str(int(current_year) - 4)  # e.g. '2022' if current is 2026
    sorted_years = sorted(y for y in annual_data.keys() if y >= min_year)[-4:]
    min_quarter = f'{min_year}Q1'
    sorted_quarters = sorted(q for q in quarter_data.keys() if q >= min_quarter)[-8:]

    def _build_row(period: str, metrics: dict[str, float | None]) -> dict:
        row_out: dict[str, object] = {'period': period}
        for mk in OUTPUT_METRICS:
            v = metrics.get(mk)
            row_out[mk] = round(v, 2) if v is not None else None
        return row_out

    annual_out = [_build_row(y, annual_data[y]) for y in sorted_years]
    quarterly_out = [_build_row(q, quarter_data[q]) for q in sorted_quarters]

    return {
        'annual': annual_out,
        'quarterly': quarterly_out,
        'metrics': OUTPUT_METRICS,
    }
