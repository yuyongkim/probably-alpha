from __future__ import annotations

import csv
from pathlib import Path

from sepa.data.universe import group_sector_name, load_sector_map_from_universe, normalize_symbol

DEFAULT_MAP = {
    '005930': 'Technology',
    '000660': 'Technology',
    '051910': 'EV Battery Chain',
}


def load_sector_map(path: Path = Path('.omx/artifacts/market-data/sector-map.csv')) -> dict[str, str]:
    out = dict(DEFAULT_MAP)
    out.update(load_sector_map_from_universe())
    if not path.exists():
        return out

    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = normalize_symbol(str(row.get('symbol', '') or ''))
            sector = group_sector_name(str(row.get('sector', '') or '').strip())
            if symbol and sector:
                out[symbol] = sector
    return out


def get_sector(symbol: str, sector_map: dict[str, str]) -> str:
    return sector_map.get(normalize_symbol(symbol), 'Other')
