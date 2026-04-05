"""Pipeline step: run Market Wizards multi-strategy screen on the daily universe.

Reads price data from the pipeline artifacts, constructs StockData objects,
and runs all wizard strategies. Output goes to wizard-screen.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from sepa.wizards import StockData, WizardScreener
from sepa.wizards.kiwoom_export import KiwoomExporter


def _load_from_db(symbol: str) -> dict:
    """Load OHLCV from ohlcv.db with open/high/low."""
    import sqlite3
    db_path = Path('data/ohlcv.db')
    if not db_path.exists():
        return {}
    try:
        conn = sqlite3.connect(str(db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT close, volume, open, high, low FROM ohlcv WHERE symbol=? ORDER BY trade_date',
            (symbol.replace('.KS', '').replace('.KQ', ''),),
        ).fetchall()
        conn.close()
    except Exception:
        return {}
    if not rows:
        return {}
    closes = [float(r['close']) for r in rows if r['close'] and float(r['close']) > 0]
    volumes = [int(r['volume'] or 0) for r in rows if r['close'] and float(r['close']) > 0]
    highs = [float(r['high'] or r['close']) for r in rows if r['close'] and float(r['close']) > 0]
    lows = [float(r['low'] or r['close']) for r in rows if r['close'] and float(r['close']) > 0]
    return {'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes}


def _load_alpha_passed(date_dir: str) -> list[dict]:
    path = Path(f'data/daily-signals/{date_dir}/alpha-passed.json')
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, dict) and 'schema_version' in data and 'items' in data:
        return data['items']
    return data if isinstance(data, list) else []


def _load_price_csv(symbol: str) -> dict:
    """Load OHLCV from market-data CSV files."""
    safe = symbol.replace('/', '_').replace('.', '_')
    candidates = [
        Path(f'data/market-data/{safe}.csv'),
        Path(f'data/cache/kiwoom/{safe}.json'),
    ]

    for path in candidates:
        if not path.exists():
            continue

        if path.suffix == '.csv':
            return _parse_csv(path)
        if path.suffix == '.json':
            return _parse_json_cache(path)

    return {}


def _parse_csv(path: Path) -> dict:
    closes, highs, lows, volumes = [], [], [], []
    lines = path.read_text(encoding='utf-8').strip().splitlines()
    for line in lines[1:]:  # skip header
        parts = line.split(',')
        if len(parts) < 3:
            continue
        try:
            c = float(parts[1])
            v = float(parts[2]) if len(parts) > 2 else 0
            closes.append(c)
            highs.append(c * 1.01)   # approximate if not available
            lows.append(c * 0.99)
            volumes.append(v)
        except (ValueError, IndexError):
            continue
    return {'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes}


def _parse_json_cache(path: Path) -> dict:
    try:
        rows = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return {}
    if not isinstance(rows, list):
        return {}
    closes, highs, lows, volumes = [], [], [], []
    for row in rows:
        c = float(row.get('close', 0))
        v = float(row.get('volume', 0))
        if c > 0:
            closes.append(c)
            highs.append(c * 1.01)
            lows.append(c * 0.99)
            volumes.append(v)
    return {'closes': closes, 'highs': highs, 'lows': lows, 'volumes': volumes}


def _load_gamma_insights(date_dir: str) -> dict[str, dict]:
    """Load gamma insights for fundamental data."""
    path = Path(f'data/daily-signals/{date_dir}/gamma-insights.json')
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return {}
    out = {}
    for item in data.get('general', []):
        out[item.get('symbol', '')] = item
    return out


def build_stock_data(symbol: str, gamma_data: dict | None = None) -> StockData | None:
    """Build StockData for a symbol from OHLCV DB (primary) or CSV fallback."""
    # Primary: read from ohlcv.db (has open/high/low/close/volume)
    price = _load_from_db(symbol)
    if not price or not price.get('closes'):
        price = _load_price_csv(symbol)
    if not price or not price.get('closes'):
        return None

    sd = StockData(
        symbol=symbol,
        closes=price['closes'],
        highs=price.get('highs', []),
        lows=price.get('lows', []),
        volumes=price.get('volumes', []),
    )

    if gamma_data:
        eps = gamma_data.get('eps_status', '')
        if eps == 'strong_growth':
            sd.eps_yoy = 30.0
            sd.eps_qoq = 25.0
        elif eps == 'positive_growth':
            sd.eps_yoy = 15.0
            sd.eps_qoq = 10.0

        sd.sector = gamma_data.get('sector', '')
        sd.market_cap = float(gamma_data.get('market_cap', float('nan')))

    return sd


def run_wizard_screen(date_dir: str) -> dict:
    """Run all wizard strategies on the daily universe.

    Returns a dict suitable for writing to wizard-screen.json.
    """
    alpha_passed = _load_alpha_passed(date_dir)
    gamma_map = _load_gamma_insights(date_dir)

    # Build universe from alpha-passed symbols
    symbols = [item['symbol'] for item in alpha_passed if 'symbol' in item]
    if not symbols:
        # Fallback: try all symbols from gamma
        symbols = list(gamma_map.keys())

    stocks: list[StockData] = []
    for sym in symbols:
        sd = build_stock_data(sym, gamma_map.get(sym))
        if sd:
            stocks.append(sd)

    if not stocks:
        return {
            'date_dir': date_dir,
            'total_stocks_screened': 0,
            'stocks_passing_any': 0,
            'results': [],
        }

    screener = WizardScreener()
    results = screener.screen_universe(stocks)
    summary = screener.summary(results)

    # Full results with details
    output = {
        'date_dir': date_dir,
        **summary,
        'results': [r.to_dict() for r in results if r.strategies_passed > 0],
    }

    return output
