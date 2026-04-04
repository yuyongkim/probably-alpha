from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


class MacroDataProvider:
    def __init__(self, cache_dir: Path = Path('data/cache/macro')) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_snapshot(self) -> dict:
        """외부 API 실패 시 캐시/기본값으로 복구하는 매크로 스냅샷."""
        snapshot = {
            'as_of': datetime.now().strftime('%Y-%m-%d'),
            'source': 'fallback',
            'wti': None,
            'fred_pmi_proxy': None,
            'ecos_rate': None,
        }

        # 1) FRED (예: DCOILWTICO)
        fred_key = os.getenv('FRED_API_KEY', '').strip()
        if fred_key:
            wti = self._fetch_fred_latest('DCOILWTICO', fred_key)
            if wti is not None:
                snapshot['wti'] = wti
                snapshot['source'] = 'api+cache'

        # 2) 캐시 병합
        cached = self._read_cache('macro_snapshot.json')
        if cached:
            for k in ['wti', 'fred_pmi_proxy', 'ecos_rate']:
                if snapshot.get(k) is None and cached.get(k) is not None:
                    snapshot[k] = cached[k]

        self._write_cache('macro_snapshot.json', snapshot)
        return snapshot

    def _fetch_fred_latest(self, series_id: str, api_key: str) -> float | None:
        url = (
            'https://api.stlouisfed.org/fred/series/observations?'
            f'series_id={series_id}&api_key={api_key}&file_type=json&sort_order=desc&limit=1'
        )
        try:
            with urlopen(url, timeout=6) as resp:  # noqa: S310
                data = json.loads(resp.read().decode('utf-8'))
            obs = data.get('observations', [])
            if not obs:
                return None
            val = obs[0].get('value', '.')
            return float(val) if val not in ('.', None, '') else None
        except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
            return None

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
