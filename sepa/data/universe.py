from __future__ import annotations

import csv
import os
from functools import lru_cache
from pathlib import Path

from sepa.data.quantdb import health as quantdb_health
from sepa.data.quantdb import read_universe as read_quantdb_universe

DEFAULT_UNIVERSE_FILE = Path('config/krx_universe.csv')
DEFAULT_SYMBOLS = ['005930.KS', '000660.KS', '051910.KS']
DEFAULT_QUANTDB_UNIVERSE_LIMIT = 2500

SECTOR_GROUP_MAP = {
    'Semiconductors': 'Technology',
    'Consumer Electronics': 'Technology',
    'Internet': 'Internet Platforms',
    'Batteries': 'EV Battery Chain',
    'Battery Materials': 'EV Battery Chain',
    'Chemicals': 'EV Battery Chain',
    'Materials': 'EV Battery Chain',
    'Biotech': 'Healthcare & Biotech',
    'Autos': 'Autos & Mobility',
    'Defense': 'Industrial & Defense',
    'Shipbuilding': 'Industrial & Defense',
    'Industrials': 'Industrial & Defense',
    'Financials': 'Financials',
}


def _universe_source() -> str:
    raw = os.getenv('SEPA_UNIVERSE_SOURCE', 'auto').strip().lower()
    return raw if raw in {'auto', 'csv', 'quantdb'} else 'auto'


def _quantdb_universe_limit() -> int:
    try:
        return int(os.getenv('SEPA_QUANTDB_UNIVERSE_LIMIT', str(DEFAULT_QUANTDB_UNIVERSE_LIMIT)).strip() or DEFAULT_QUANTDB_UNIVERSE_LIMIT)
    except ValueError:
        return DEFAULT_QUANTDB_UNIVERSE_LIMIT


def _quantdb_markets() -> tuple[str, ...]:
    raw = os.getenv('SEPA_QUANTDB_UNIVERSE_MARKETS', '코스피,코스닥').strip()
    return tuple(part.strip() for part in raw.split(',') if part.strip())


def _universe_file(path: Path | None = None) -> Path:
    if path is not None:
        return path
    env_path = os.getenv('SEPA_UNIVERSE_FILE', '').strip()
    return Path(env_path) if env_path else DEFAULT_UNIVERSE_FILE


def normalize_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    if s.startswith('A') and len(s) >= 7 and s[1:7].isdigit():
        return s[1:7]
    if '.' in s:
        left = s.split('.', 1)[0]
        if left.isdigit():
            return left
    return s


def group_sector_name(sector: str) -> str:
    raw = str(sector or '').strip()
    if not raw:
        return 'Other'
    return SECTOR_GROUP_MAP.get(raw, raw)


def _read_csv_universe(path: Path | None = None) -> list[dict[str, str]]:
    file_path = _universe_file(path)
    if not file_path.exists():
        return []

    out: list[dict[str, str]] = []
    seen: set[str] = set()
    with file_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = str(row.get('symbol', '') or '').strip().upper()
            if not symbol or symbol in seen:
                continue

            industry = str(row.get('sector', '') or '').strip() or 'Other'
            sector = group_sector_name(industry)
            item = {
                'symbol': symbol,
                'name': str(row.get('name', '') or '').strip() or symbol,
                'sector': sector,
                'sector_group': sector,
                'industry': industry,
                'sample_profile': str(row.get('sample_profile', '') or '').strip() or 'steady',
                'eps_profile': str(row.get('eps_profile', '') or '').strip() or 'positive_growth',
            }
            out.append(item)
            seen.add(symbol)
    return out


@lru_cache(maxsize=8)
def _cached_quantdb_universe(limit: int, markets_key: str) -> tuple[dict[str, str], ...]:
    records = read_quantdb_universe(limit=limit, markets=tuple(part for part in markets_key.split('|') if part))
    normalized = []
    for row in records:
        sector = group_sector_name(str(row.get('sector', '') or '').strip() or 'Other')
        normalized.append(
            {
                'symbol': str(row.get('symbol', '') or '').strip().upper(),
                'name': str(row.get('name', '') or '').strip() or str(row.get('symbol', '') or '').strip().upper(),
                'sector': sector,
                'sector_group': sector,
                'industry': str(row.get('industry', '') or row.get('sector', '') or '').strip() or sector,
                'sample_profile': str(row.get('sample_profile', '') or '').strip() or 'steady',
                'eps_profile': str(row.get('eps_profile', '') or '').strip() or 'positive_growth',
            }
        )
    return tuple(normalized)


def load_universe(path: Path | None = None) -> list[dict[str, str]]:
    if path is None:
        source = _universe_source()
        quantdb_ready = quantdb_health().get('has_quantking_snapshot')
        if source == 'quantdb' or (source == 'auto' and quantdb_ready):
            records = list(_cached_quantdb_universe(_quantdb_universe_limit(), '|'.join(_quantdb_markets())))
            if records:
                return records
    return _read_csv_universe(path=path)


def load_symbols(path: Path | None = None) -> list[str]:
    raw = os.getenv('SEPA_SYMBOLS', '').strip()
    if raw:
        return [s.strip().upper() for s in raw.split(',') if s.strip()]

    records = load_universe(path=path)
    if records:
        return [row['symbol'] for row in records]
    return list(DEFAULT_SYMBOLS)


def load_sector_map_from_universe(path: Path | None = None) -> dict[str, str]:
    return {normalize_symbol(row['symbol']): row['sector'] for row in load_universe(path=path)}


@lru_cache(maxsize=4)
def _cached_symbol_meta_map(cache_key: str, path_str: str) -> dict[str, dict[str, str]]:
    path = Path(path_str) if path_str else None
    mapping: dict[str, dict[str, str]] = {}
    for row in load_universe(path=path):
        payload = {
            'name': row.get('name', row['symbol']),
            'sector': row.get('sector', 'Other'),
            'industry': row.get('industry', row.get('sector', 'Other')),
        }
        mapping[row['symbol']] = payload
        mapping[normalize_symbol(row['symbol'])] = payload
    return mapping


def load_symbol_meta_map(path: Path | None = None) -> dict[str, dict[str, str]]:
    if path is not None and _universe_file(path).exists():
        cache_key = f'csv:{_universe_file(path).resolve()}'
        resolved = str(_universe_file(path).resolve())
    else:
        cache_key = f'{_universe_source()}:{_quantdb_universe_limit()}:{",".join(_quantdb_markets())}'
        resolved = ''
    return dict(_cached_symbol_meta_map(cache_key, resolved))


def load_symbol_name_map(path: Path | None = None) -> dict[str, str]:
    return {key: value['name'] for key, value in load_symbol_meta_map(path=path).items()}


def get_symbol_name(symbol: str, path: Path | None = None) -> str:
    if not symbol:
        return ''
    mapping = load_symbol_meta_map(path=path)
    payload = mapping.get(symbol) or mapping.get(normalize_symbol(symbol))
    name = payload.get('name', '') if payload else ''
    if name and name != symbol:
        return name
    # Fallback: try QuantDB snapshot for unmapped symbols
    try:
        from sepa.data.quantdb import read_company_snapshot
        snap = read_company_snapshot(symbol)
        if snap and snap.get('name'):
            return snap['name']
    except Exception:  # noqa: BLE001
        pass
    return symbol


def get_symbol_sector(symbol: str, path: Path | None = None) -> str:
    if not symbol:
        return 'Other'
    mapping = load_symbol_meta_map(path=path)
    payload = mapping.get(symbol) or mapping.get(normalize_symbol(symbol))
    return payload.get('sector', 'Other') if payload else 'Other'


def get_symbol_industry(symbol: str, path: Path | None = None) -> str:
    if not symbol:
        return 'Other'
    mapping = load_symbol_meta_map(path=path)
    payload = mapping.get(symbol) or mapping.get(normalize_symbol(symbol))
    return payload.get('industry', payload.get('sector', 'Other')) if payload else 'Other'
