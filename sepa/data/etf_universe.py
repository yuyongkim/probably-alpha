from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path


DEFAULT_ETF_UNIVERSE_PATH = Path('config/krx_etf_universe.csv')


def _normalize_symbol(symbol: str) -> str:
    value = str(symbol or '').strip().upper()
    if value.startswith('A') and len(value) >= 7 and value[1:7].isdigit():
        return value[1:7]
    if '.' in value:
        left = value.split('.', 1)[0]
        if left.isdigit():
            return left
    return value


@lru_cache(maxsize=4)
def load_etf_universe(path_str: str = str(DEFAULT_ETF_UNIVERSE_PATH)) -> list[dict]:
    path = Path(path_str)
    if not path.exists():
        return []

    items: list[dict] = []
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            symbol = _normalize_symbol(row.get('symbol', ''))
            if not symbol:
                continue
            items.append(
                {
                    'symbol': symbol,
                    'name': str(row.get('name', '') or symbol).strip() or symbol,
                    'asset_class': str(row.get('asset_class', '') or '').strip() or 'equity',
                    'theme': str(row.get('theme', '') or '').strip() or '기타',
                    'risk_profile': str(row.get('risk_profile', '') or '').strip() or 'balanced',
                    'leverage': str(row.get('leverage', 'N') or 'N').strip().upper() == 'Y',
                    'inverse': str(row.get('inverse', 'N') or 'N').strip().upper() == 'Y',
                    'benchmark_symbol': _normalize_symbol(row.get('benchmark_symbol', '') or symbol),
                }
            )
    return items


def load_etf_symbols(path: Path = DEFAULT_ETF_UNIVERSE_PATH) -> list[str]:
    return [item['symbol'] for item in load_etf_universe(str(path))]


def get_etf_meta(symbol: str, path: Path = DEFAULT_ETF_UNIVERSE_PATH) -> dict:
    normalized = _normalize_symbol(symbol)
    for item in load_etf_universe(str(path)):
        if item['symbol'] == normalized:
            return item
    return {}
