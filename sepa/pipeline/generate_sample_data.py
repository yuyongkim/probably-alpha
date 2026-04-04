from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from sepa.data.universe import load_universe

OHLCV_DIR = Path('data/market-data/ohlcv')
EPS_PATH = Path('data/market-data/fundamentals/eps.csv')
MIN_HISTORY_DAYS = 1600
MIN_EPS_QUARTERS = 20


def _date_series(length: int = MIN_HISTORY_DAYS) -> list[str]:
    cursor = date.today()
    out: list[str] = []
    while len(out) < length:
        if cursor.weekday() < 5:
            out.append(cursor.isoformat())
        cursor -= timedelta(days=1)
    out.reverse()
    return out


def _write_ohlcv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'close', 'volume'])
        writer.writeheader()
        writer.writerows(rows)


def _read_ohlcv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open('r', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _history_profile(profile: str) -> tuple[float, float, int]:
    if profile == 'vcp_leader':
        return (0.0014, 0.012, 780_000)
    if profile == 'strong_trend':
        return (0.0017, 0.015, 1_400_000)
    if profile == 'recovery':
        return (0.0011, 0.017, 1_050_000)
    return (0.0008, 0.010, 950_000)


def _previous_business_dates(before_day: date, length: int) -> list[str]:
    cursor = before_day - timedelta(days=1)
    out: list[str] = []
    while len(out) < length:
        if cursor.weekday() < 5:
            out.append(cursor.isoformat())
        cursor -= timedelta(days=1)
    out.reverse()
    return out


def _extend_rows_backward(rows: list[dict], profile: str, seed: int, target_length: int) -> list[dict]:
    if not rows or len(rows) >= target_length:
        return rows

    drift, noise, base_volume = _history_profile(profile)
    random.seed(seed * 1009 + len(rows))

    first_date = datetime.strptime(str(rows[0]['date']).strip(), '%Y-%m-%d').date()
    current_close = max(8.0, float(rows[0].get('close', 0.0) or 0.0))
    current_volume = max(10_000, int(float(rows[0].get('volume', 0.0) or 0.0)))
    missing = target_length - len(rows)
    dates = _previous_business_dates(first_date, missing)
    prefix_desc: list[dict] = []

    for day in reversed(dates):
        move = drift + random.uniform(-noise, noise)
        denom = max(0.84, 1.0 + move)
        previous_close = max(6.0, current_close / denom)
        volume_anchor = current_volume if current_volume > 0 else base_volume
        previous_volume = int(max(10_000, volume_anchor * random.uniform(0.84, 1.16)))
        prefix_desc.append({'date': day, 'close': round(previous_close, 2), 'volume': previous_volume})
        current_close = previous_close
        current_volume = previous_volume

    prefix_desc.reverse()
    return prefix_desc + rows


def _profile_rows(profile: str, seed: int, length: int = MIN_HISTORY_DAYS) -> list[dict]:
    if profile == 'vcp_leader':
        return _vcp_rows(seed=seed, length=length)
    if profile == 'strong_trend':
        return _trend_rows(seed=seed, length=length, drift=0.0017, noise=0.015, volume=1_400_000)
    if profile == 'recovery':
        return _recovery_rows(seed=seed, length=length)
    return _trend_rows(seed=seed, length=length, drift=0.0008, noise=0.01, volume=950_000)


def _trend_rows(seed: int, length: int, drift: float, noise: float, volume: int) -> list[dict]:
    random.seed(seed)
    price = 55.0 + seed * 4.0
    dates = _date_series(length)
    rows = []
    for idx, day in enumerate(dates):
        price = max(12.0, price * (1 + drift + random.uniform(-noise, noise)))
        vol = int(volume * random.uniform(0.82, 1.18))
        rows.append({'date': day, 'close': round(price, 2), 'volume': max(10_000, vol)})
    return rows


def _recovery_rows(seed: int, length: int) -> list[dict]:
    random.seed(seed)
    price = 80.0 + seed * 3.0
    dates = _date_series(length)
    rows = []
    for idx, day in enumerate(dates):
        if idx < 120:
            drift = -0.0008
            noise = 0.018
            volume = 1_100_000
        elif idx < 190:
            drift = 0.0004
            noise = 0.012
            volume = 900_000
        else:
            drift = 0.0019
            noise = 0.011
            volume = 1_200_000
        price = max(10.0, price * (1 + drift + random.uniform(-noise, noise)))
        vol = int(volume * random.uniform(0.8, 1.2))
        rows.append({'date': day, 'close': round(price, 2), 'volume': max(10_000, vol)})
    return rows


def _vcp_rows(seed: int, length: int) -> list[dict]:
    random.seed(seed)
    dates = _date_series(length)
    rows = []
    price = 70.0 + seed * 2.5

    warmup = max(160, length - 140)
    for idx, day in enumerate(dates[:warmup]):
        price = max(12.0, price * (1 + 0.0014 + random.uniform(-0.012, 0.012)))
        vol = int(1_300_000 * random.uniform(0.86, 1.14))
        rows.append({'date': day, 'close': round(price, 2), 'volume': max(10_000, vol)})

    amps = [0.16, 0.11, 0.07, 0.04]
    for amp in amps:
        for day in dates[len(rows) : min(len(rows) + 8, length)]:
            price = max(12.0, price * (1 + 0.003 + random.uniform(-0.008, 0.008)))
            vol = int(900_000 * random.uniform(0.88, 1.08))
            rows.append({'date': day, 'close': round(price, 2), 'volume': max(10_000, vol)})
        for day in dates[len(rows) : min(len(rows) + 12, length)]:
            price = max(12.0, price * (1 - amp / 12 + random.uniform(-0.004, 0.004)))
            vol = int(650_000 * random.uniform(0.72, 0.98))
            rows.append({'date': day, 'close': round(price, 2), 'volume': max(10_000, vol)})

    while len(rows) < length:
        day = dates[len(rows)]
        price = max(12.0, price * (1 + 0.0025 + random.uniform(-0.007, 0.007)))
        vol = int(760_000 * random.uniform(0.85, 1.05))
        rows.append({'date': day, 'close': round(price, 2), 'volume': max(10_000, vol)})

    return rows[:length]


def _load_existing_eps() -> dict[str, list[dict]]:
    if not EPS_PATH.exists():
        return {}
    out: dict[str, list[dict]] = {}
    with EPS_PATH.open('r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = str(row.get('symbol', '') or '').strip().upper()
            if not symbol:
                continue
            out.setdefault(symbol, []).append(
                {
                    'symbol': symbol,
                    'period': str(row.get('period', '') or '').strip(),
                    'eps': str(row.get('eps', '') or '').strip(),
                    'eps_yoy': str(row.get('eps_yoy', '') or '').strip(),
                }
            )
    return out


def _recent_quarters(count: int = MIN_EPS_QUARTERS) -> list[str]:
    today = date.today()
    quarter = ((today.month - 1) // 3)
    year = today.year
    out: list[str] = []
    for _ in range(count):
        if quarter == 0:
            year -= 1
            quarter = 4
        out.append(f'{year}Q{quarter}')
        quarter -= 1
    out.reverse()
    return out


def _eps_rows(symbol: str, profile: str, seed: int, quarters: int = MIN_EPS_QUARTERS) -> list[dict]:
    base = 650 + seed * 48
    periods = _recent_quarters(quarters)

    if profile == 'strong_growth':
        yoy_series = [max(12, min(38, 10 + idx * 1.3 + (idx % 4))) for idx in range(quarters)]
        growth_step = 0.028
    elif profile == 'weak_or_negative':
        yoy_series = [max(-18, -10 + idx * 0.35) for idx in range(quarters)]
        growth_step = 0.004
    else:
        yoy_series = [max(3, min(20, 5 + idx * 0.6 + ((idx + 1) % 3))) for idx in range(quarters)]
        growth_step = 0.015

    rows = []
    eps = float(base)
    for idx, (period, yoy) in enumerate(zip(periods, yoy_series, strict=False), 1):
        eps *= 1 + growth_step + (0.004 if idx % 4 == 0 else 0.0)
        rows.append({'symbol': symbol, 'period': period, 'eps': round(eps, 2), 'eps_yoy': round(yoy, 2)})
    return rows


def _write_eps(records: list[dict], overwrite: bool) -> None:
    existing = _load_existing_eps()
    for idx, record in enumerate(records, 1):
        symbol = record['symbol']
        if existing.get(symbol) and not overwrite and len(existing[symbol]) >= MIN_EPS_QUARTERS:
            continue
        existing[symbol] = _eps_rows(symbol, record.get('eps_profile', 'positive_growth'), idx)

    EPS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EPS_PATH.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'period', 'eps', 'eps_yoy'])
        writer.writeheader()
        for symbol in sorted(existing):
            for row in existing[symbol]:
                writer.writerow(row)


def generate_for_symbols(
    symbols: list[str] | None = None,
    *,
    overwrite: bool = False,
    source_rows: dict[str, list[dict]] | None = None,
    min_length: int = MIN_HISTORY_DAYS,
) -> list[str]:
    universe = load_universe()
    records_by_symbol = {row['symbol']: row for row in universe}
    selected_symbols = symbols or [row['symbol'] for row in universe]
    generated: list[str] = []
    eps_records: list[dict] = []

    for idx, symbol in enumerate(selected_symbols, 1):
        record = records_by_symbol.get(
            symbol,
            {
                'symbol': symbol,
                'sector': 'Other',
                'sample_profile': 'steady',
                'eps_profile': 'positive_growth',
            },
        )
        path = OHLCV_DIR / f'{symbol}.csv'
        if path.exists() and not overwrite and not (source_rows and symbol in source_rows):
            eps_records.append(record)
            continue

        rows = source_rows.get(symbol) if source_rows else None
        if not rows:
            rows = _profile_rows(record.get('sample_profile', 'steady'), seed=idx, length=min_length)
        _write_ohlcv(path, rows)
        generated.append(symbol)
        eps_records.append(record)

    if eps_records:
        _write_eps(eps_records, overwrite=False)
    return generated


def ensure_min_history(symbols: list[str] | None = None, min_length: int = MIN_HISTORY_DAYS) -> list[str]:
    universe = load_universe()
    records_by_symbol = {row['symbol']: row for row in universe}
    selected_symbols = symbols or [row['symbol'] for row in universe]
    extended: list[str] = []
    eps_records: list[dict] = []

    for idx, symbol in enumerate(selected_symbols, 1):
        record = records_by_symbol.get(
            symbol,
            {
                'symbol': symbol,
                'sector': 'Other',
                'sample_profile': 'steady',
                'eps_profile': 'positive_growth',
            },
        )
        path = OHLCV_DIR / f'{symbol}.csv'
        rows = _read_ohlcv(path)
        if not rows:
            generate_for_symbols([symbol], overwrite=True, min_length=min_length)
            extended.append(symbol)
            eps_records.append(record)
            continue

        if len(rows) < min_length:
            normalized = [
                {
                    'date': str(row.get('date', '')).strip(),
                    'close': float(str(row.get('close', 0) or 0).replace(',', '')),
                    'volume': int(float(str(row.get('volume', 0) or 0).replace(',', ''))),
                }
                for row in rows
                if str(row.get('date', '')).strip()
            ]
            extended_rows = _extend_rows_backward(
                normalized,
                profile=record.get('sample_profile', 'steady'),
                seed=idx,
                target_length=min_length,
            )
            _write_ohlcv(path, extended_rows)
            extended.append(symbol)

        eps_records.append(record)

    if eps_records:
        _write_eps(eps_records, overwrite=False)
    return extended


def main() -> None:
    symbols = [row['symbol'] for row in load_universe()]
    generated = generate_for_symbols(symbols, overwrite=False, min_length=MIN_HISTORY_DAYS)
    extended = ensure_min_history(symbols, min_length=MIN_HISTORY_DAYS)
    print(f'[OK] sample universe generated at {OHLCV_DIR} | generated={len(generated)} extended={len(extended)}')


if __name__ == '__main__':
    main()
