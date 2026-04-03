from __future__ import annotations

import csv
import os
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from sepa.data.price_history import normalize_date_token
from sepa.data.quantdb import health as quantdb_health
from sepa.data.quantdb import read_eps_rows as read_quantdb_eps_rows


EPS_PATH = Path('.omx/artifacts/market-data/fundamentals/eps.csv')


def _to_num(value) -> float:
    try:
        return float(str(value).replace(',', ''))
    except Exception:
        return 0.0


def _period_available_token(period: str) -> str:
    raw = str(period or '').strip().upper()
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


def read_eps_series(
    symbol: str,
    path: Path = EPS_PATH,
    as_of_date: str | None = None,
) -> list[dict]:
    return [
        {
            'period': row[0],
            'available_date': row[1],
            'eps': row[2],
            'eps_yoy': row[3],
        }
        for row in _read_eps_series_cached(
            symbol.upper(),
            str(path),
            _path_mtime_ns(path),
            normalize_date_token(as_of_date),
            str(os.getenv('SEPA_EPS_SOURCE', 'auto') or 'auto').strip().lower(),
            bool(quantdb_health().get('has_financials_quarterly')),
        )
    ]


@lru_cache(maxsize=512)
def _read_eps_series_cached(
    symbol: str,
    path_str: str,
    path_mtime_ns: int,
    cutoff: str,
    source_raw: str,
    quantdb_ready: bool,
) -> tuple[tuple[str, str, float, float], ...]:
    source = str(os.getenv('SEPA_EPS_SOURCE', 'auto') or 'auto').strip().lower()
    if source_raw:
        source = source_raw
    if source not in {'auto', 'csv', 'quantdb'}:
        source = 'auto'

    quantdb_rows: list[dict] = []
    if source == 'quantdb' or (source == 'auto' and quantdb_ready):
        quantdb_rows = read_quantdb_eps_rows(symbol, as_of_date=cutoff or None)

    csv_rows: list[dict] = []
    path = Path(path_str)
    if path.exists():
        with path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if str(row.get('symbol', '')).strip().upper() != symbol:
                    continue

                period = str(row.get('period', '')).strip()
                available_token = _period_available_token(period)
                if cutoff and available_token and available_token > cutoff:
                    continue

                csv_rows.append(
                    {
                        'period': period,
                        'available_date': available_token,
                        'eps': _to_num(row.get('eps')),
                        'eps_yoy': _to_num(row.get('eps_yoy')),
                    }
                )

    if source == 'csv':
        return tuple(
            (row['period'], row['available_date'], row['eps'], row['eps_yoy'])
            for row in csv_rows
        )
    if source == 'quantdb':
        return tuple(
            (
                str(row.get('period', '')).strip(),
                str(row.get('available_date', '')).strip(),
                _to_num(row.get('eps')),
                _to_num(row.get('eps_yoy')),
            )
            for row in quantdb_rows
        )

    merged: dict[str, dict] = {}
    for row in quantdb_rows:
        period = str(row.get('period', '')).strip()
        if period:
            merged[period] = row
    for row in csv_rows:
        period = str(row.get('period', '')).strip()
        if period:
            merged[period] = row
    return tuple(
        (
            key,
            str(merged[key].get('available_date', '')).strip(),
            _to_num(merged[key].get('eps')),
            _to_num(merged[key].get('eps_yoy')),
        )
        for key in sorted(merged)
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
