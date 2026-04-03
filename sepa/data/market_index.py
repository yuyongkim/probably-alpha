from __future__ import annotations

import csv
from pathlib import Path

from sepa.data.price_history import format_date_token, is_business_date_token, normalize_date_token, read_price_series_from_path


INDEX_SPECS = {
    'KOSPI': {'ticker': '^KS11', 'label': 'KOSPI'},
    'KOSDAQ': {'ticker': '^KQ11', 'label': 'KOSDAQ'},
}
INDEX_DIR = Path('.omx/artifacts/market-data/index')


def _market_key(market: str | None) -> str:
    token = str(market or 'KOSPI').strip().upper()
    return token if token in INDEX_SPECS else 'KOSPI'


def market_index_path(market: str | None, data_dir: Path = INDEX_DIR) -> Path:
    key = _market_key(market)
    return data_dir / f'{key}.csv'


def fetch_market_index_rows(market: str | None, period: str = '6y') -> list[dict]:
    key = _market_key(market)
    spec = INDEX_SPECS[key]
    try:
        import yfinance as yf
    except Exception:
        return []

    try:
        history = yf.Ticker(spec['ticker']).history(period=period, interval='1d', auto_adjust=False)
    except Exception:
        return []
    if history is None or history.empty:
        return []

    rows: list[dict] = []
    for index, row in history.iterrows():
        token = normalize_date_token(index.strftime('%Y%m%d'))
        if not is_business_date_token(token):
            continue
        close = float(row.get('Close', 0.0) or 0.0)
        if close <= 0:
            continue
        volume = float(row.get('Volume', 0.0) or 0.0)
        rows.append(
            {
                'date': format_date_token(token),
                'close': round(close, 4),
                'volume': int(volume),
            }
        )
    return rows


def write_market_index_rows(market: str | None, rows: list[dict], data_dir: Path = INDEX_DIR) -> Path:
    path = market_index_path(market, data_dir=data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['date', 'close', 'volume'])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    'date': row.get('date', ''),
                    'close': row.get('close', 0.0),
                    'volume': row.get('volume', 0),
                }
            )
    return path


def ensure_market_index_history(markets: list[str] | None = None, period: str = '6y', data_dir: Path = INDEX_DIR) -> dict[str, int]:
    targets = markets or list(INDEX_SPECS)
    updated: dict[str, int] = {}
    for market in targets:
        key = _market_key(market)
        rows = fetch_market_index_rows(key, period=period)
        if not rows:
            continue
        write_market_index_rows(key, rows, data_dir=data_dir)
        updated[key] = len(rows)
    return updated


def read_market_index_series(market: str | None, as_of_date: str | None = None, data_dir: Path = INDEX_DIR) -> list[dict]:
    path = market_index_path(market, data_dir=data_dir)
    if not path.exists():
        ensure_market_index_history([_market_key(market)], data_dir=data_dir)
    return read_price_series_from_path(path, as_of_date=as_of_date)
