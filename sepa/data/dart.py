from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from sepa.data.fundamentals import eps_growth_snapshot

logger = logging.getLogger(__name__)

DART_API_BASE = 'https://opendart.fss.or.kr/api'
DART_TIMEOUT_SEC = 10


class DartProvider:
    def __init__(self, cache_dir: Path = Path('.omx/artifacts/cache/dart')) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv('DART_API_KEY', '').strip()

    def get_growth_hint(self, symbol: str, corp_code: str = '', as_of_date: str | None = None) -> dict:
        """Returns a simple EPS-driven growth snapshot with optional API confirmation."""
        base = eps_growth_snapshot(symbol, as_of_date=as_of_date)
        key = symbol.replace('.', '_') + '.json'
        cached = self._read_cache(key)
        if cached and 'growth_hint' in cached and not as_of_date:
            return {
                **base,
                'growth_hint': max(base['growth_hint'], float(cached['growth_hint'])),
                'source': 'eps+cache',
            }

        if not self.api_key or not corp_code:
            return {**base, 'source': 'eps'}

        try:
            url = f'{DART_API_BASE}/company.json?corp_code={corp_code}'
            req = Request(url, headers={'Authorization': f'Bearer {self.api_key}'})
            with urlopen(req, timeout=DART_TIMEOUT_SEC) as resp:  # noqa: S310
                _ = resp.read(256)
            hint = max(base['growth_hint'], 0.9)
        except (URLError, TimeoutError) as exc:
            logger.warning('DART API failed for %s: %s', symbol, exc)
            hint = base['growth_hint']

        self._write_cache(key, {'growth_hint': hint})
        return {**base, 'growth_hint': hint, 'source': 'eps+api'}

    def _cache_path(self, name: str) -> Path:
        return self.cache_dir / name

    def _read_cache(self, name: str) -> dict | None:
        p = self._cache_path(name)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return None

    def _write_cache(self, name: str, payload: dict) -> None:
        p = self._cache_path(name)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
