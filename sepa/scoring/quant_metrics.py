"""Quantitative metrics computed from Naver-sourced financial data.

All calculations use ohlcv.db financials table.
No external API calls — pure SQL + math.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path('data/sepa.db')


def _connect() -> sqlite3.Connection | None:
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _get_metric(conn: sqlite3.Connection, symbol: str, period: str, metric: str) -> float | None:
    row = conn.execute(
        'SELECT value FROM financials WHERE symbol = ? AND period = ? AND metric = ?',
        (symbol, period, metric),
    ).fetchone()
    return float(row['value']) if row else None


def compute_stock_quant(symbol: str) -> dict:
    """Compute all quant metrics for a stock from DB data.

    Returns dict with growth rates, margins, valuation ratios.
    """
    conn = _connect()
    if conn is None:
        return {}
    code = symbol.replace('.KS', '').replace('.KQ', '')

    try:
        # Get available periods
        annual_periods = [r['period'] for r in conn.execute(
            "SELECT DISTINCT period FROM financials WHERE symbol = ? AND period_type = 'annual' AND length(period) = 4 ORDER BY period",
            (code,),
        ).fetchall()]

        quarterly_periods = [r['period'] for r in conn.execute(
            "SELECT DISTINCT period FROM financials WHERE symbol = ? AND period_type = 'quarterly' ORDER BY period",
            (code,),
        ).fetchall()]

        result: dict = {
            'symbol': symbol,
            'annual_periods': annual_periods[-4:],
            'quarterly_periods': quarterly_periods[-8:],
        }

        # Annual growth rates
        if len(annual_periods) >= 2:
            latest = annual_periods[-1]
            prev = annual_periods[-2]
            result['revenue_yoy'] = _growth_rate(conn, code, prev, latest, '매출액')
            result['op_profit_yoy'] = _growth_rate(conn, code, prev, latest, '영업이익')
            result['net_income_yoy'] = _growth_rate(conn, code, prev, latest, '당기순이익')
            result['eps_yoy'] = _growth_rate(conn, code, prev, latest, 'EPS')

        # Quarterly growth rates (QoQ + YoY)
        if len(quarterly_periods) >= 2:
            latest_q = quarterly_periods[-1]
            prev_q = quarterly_periods[-2]
            result['revenue_qoq'] = _growth_rate(conn, code, prev_q, latest_q, '매출액')
            result['op_profit_qoq'] = _growth_rate(conn, code, prev_q, latest_q, '영업이익')
            result['eps_qoq'] = _growth_rate(conn, code, prev_q, latest_q, 'EPS')

        # YoY quarterly (same quarter last year)
        if len(quarterly_periods) >= 5:
            latest_q = quarterly_periods[-1]
            # Find same quarter last year
            lq_year = latest_q[:4]
            lq_num = latest_q[5:]  # Q1, Q2, etc.
            yoy_q = f'{int(lq_year) - 1}Q{lq_num[1:]}'  # e.g. 2024Q3
            if yoy_q in quarterly_periods:
                result['revenue_qoq_yoy'] = _growth_rate(conn, code, yoy_q, latest_q, '매출액')
                result['eps_qoq_yoy'] = _growth_rate(conn, code, yoy_q, latest_q, 'EPS')

        # Latest margins & ratios
        latest_period = annual_periods[-1] if annual_periods else (quarterly_periods[-1] if quarterly_periods else '')
        if latest_period:
            result['opm'] = _get_metric(conn, code, latest_period, '영업이익률')
            result['npm'] = _get_metric(conn, code, latest_period, '순이익률')
            result['roe'] = _get_metric(conn, code, latest_period, 'ROE')
            result['roa'] = _get_metric(conn, code, latest_period, 'ROA')
            result['debt_ratio'] = _get_metric(conn, code, latest_period, '부채비율')
            result['per'] = _get_metric(conn, code, latest_period, 'PER')
            result['pbr'] = _get_metric(conn, code, latest_period, 'PBR')
            result['eps'] = _get_metric(conn, code, latest_period, 'EPS')

        # EPS acceleration (is growth accelerating?)
        if len(quarterly_periods) >= 4:
            q_eps = []
            for q in quarterly_periods[-4:]:
                v = _get_metric(conn, code, q, 'EPS')
                if v is not None:
                    q_eps.append(v)
            if len(q_eps) >= 4:
                recent_growth = (q_eps[-1] / q_eps[-2] - 1) if q_eps[-2] and q_eps[-2] != 0 else None
                older_growth = (q_eps[-3] / q_eps[-4] - 1) if q_eps[-4] and q_eps[-4] != 0 else None
                if recent_growth is not None and older_growth is not None:
                    result['eps_acceleration'] = round((recent_growth - older_growth) * 100, 1)

        # PEG ratio (PER / EPS growth)
        per = result.get('per')
        eps_yoy = result.get('eps_yoy')
        if per and eps_yoy and eps_yoy > 0:
            result['peg'] = round(per / eps_yoy, 2)

        # Revenue trend (consecutive growth quarters)
        if len(quarterly_periods) >= 4:
            rev_streak = 0
            for j in range(len(quarterly_periods) - 1, 0, -1):
                curr_rev = _get_metric(conn, code, quarterly_periods[j], '매출액')
                prev_rev = _get_metric(conn, code, quarterly_periods[j - 1], '매출액')
                if curr_rev and prev_rev and curr_rev > prev_rev:
                    rev_streak += 1
                else:
                    break
            result['revenue_growth_streak'] = rev_streak

        # Round all floats
        for k, v in result.items():
            if isinstance(v, float):
                result[k] = round(v, 2)

        return result
    finally:
        conn.close()


def _growth_rate(conn: sqlite3.Connection, symbol: str, period_from: str, period_to: str, metric: str) -> float | None:
    v_from = _get_metric(conn, symbol, period_from, metric)
    v_to = _get_metric(conn, symbol, period_to, metric)
    if v_from is None or v_to is None or v_from == 0:
        return None
    return round((v_to / v_from - 1) * 100, 2)


def compute_universe_quant(symbols: list[str] | None = None) -> list[dict]:
    """Compute quant metrics for multiple stocks."""
    conn = _connect()
    if conn is None:
        return []
    if symbols is None:
        symbols = [r['symbol'] for r in conn.execute('SELECT symbol FROM symbol_meta ORDER BY symbol').fetchall()]
    conn.close()
    return [compute_stock_quant(s) for s in symbols]
