from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sepa.data.symbols import to_kiwoom_symbol

logger = logging.getLogger(__name__)


KIWOOM_BASE_URL = 'https://api.kiwoom.com'
DEFAULT_TOKEN_PATH = '/oauth2/token'
DEFAULT_OHLCV_PATH = '/api/dostk/mrkcond'
DEFAULT_OHLCV_API_ID = 'ka10086'


@dataclass
class KiwoomConfig:
    app_key: str
    secret_key: str
    market_type: str
    base_url: str
    token_url: str
    ohlcv_url: str
    ohlcv_api_id: str
    query_date: str


class KiwoomProvider:
    """Kiwoom REST adapter with default endpoints and stale-cache refresh."""

    ROW_FIELD_CANDIDATES = {
        'date': ['date', 'trade_date', 'stck_bsop_date', 'bas_dt', 'dt', '일자'],
        'close': ['close_pric', 'close', 'stck_clpr', 'clpr', '종가'],
        'volume': ['trde_qty', 'trade_qty', 'acml_vol', 'volume', 'trdvol', '거래량'],
    }

    ENVELOPE_KEYS = ['daly_stkpc', 'data', 'output', 'items', 'result', 'list']

    def __init__(self, cache_dir: Path = Path('.omx/artifacts/cache/kiwoom')) -> None:
        self.cfg = KiwoomConfig(
            app_key=os.getenv('KIWOOM_APP_KEY', '').strip(),
            secret_key=os.getenv('KIWOOM_SECRET_KEY', '').strip(),
            market_type=os.getenv('KIWOOM_MARKET_TYPE', '0').strip(),
            base_url=os.getenv('KIWOOM_BASE_URL', KIWOOM_BASE_URL).strip().rstrip('/'),
            token_url=os.getenv('KIWOOM_TOKEN_URL', '').strip(),
            ohlcv_url=os.getenv('KIWOOM_OHLCV_URL', '').strip(),
            ohlcv_api_id=os.getenv('KIWOOM_OHLCV_API_ID', DEFAULT_OHLCV_API_ID).strip() or DEFAULT_OHLCV_API_ID,
            query_date=os.getenv('KIWOOM_QUERY_DATE', '').strip(),
        )
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir = Path('.omx/artifacts/audit-logs')
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def health(self) -> dict:
        return {
            'has_app_key': bool(self.cfg.app_key),
            'has_secret_key': bool(self.cfg.secret_key),
            'has_token_endpoint': bool(self._token_endpoint()),
            'has_ohlcv_endpoint': bool(self._ohlcv_endpoint()),
            'ohlcv_api_id': self.cfg.ohlcv_api_id,
            'market_type': self.cfg.market_type,
            'base_url': self.cfg.base_url,
        }

    def fetch_ohlcv(self, symbol: str, limit: int = 300) -> list[dict]:
        cached = self._read_cache(symbol)
        if self._cache_is_fresh(cached, limit):
            return self._limit_rows(cached, limit)

        token = self._issue_token()
        if not token:
            self._audit('kiwoom', f'token issue failed: {symbol}')
            return self._limit_rows(cached, limit)

        payload = {
            'mrkt_tp': self._market_code(symbol),
            'stk_cd': to_kiwoom_symbol(symbol),
            'qry_dt': self._query_date_token(),
            'indc_tp': '0',
        }
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'Bearer {token}',
            'api-id': self.cfg.ohlcv_api_id,
        }

        data = self._post_json(
            self._ohlcv_endpoint(),
            payload,
            headers,
            retries=3,
            component='kiwoom_ohlcv',
        )
        rows = self._normalize_rows(data)
        if not rows:
            self._audit('kiwoom', f'normalize returned empty: {symbol}')
            return self._limit_rows(cached, limit)

        merged = self._merge_rows(cached, rows)
        self._write_cache(symbol, merged)
        return self._limit_rows(merged, limit)

    def _issue_token(self) -> str:
        if not (self.cfg.app_key and self.cfg.secret_key and self._token_endpoint()):
            return ''

        payload = {
            'grant_type': 'client_credentials',
            'appkey': self.cfg.app_key,
            # Kiwoom examples use `secretkey`; some wrappers still expect `appsecret`.
            'secretkey': self.cfg.secret_key,
            'appsecret': self.cfg.secret_key,
        }
        data = self._post_json(
            self._token_endpoint(),
            payload,
            {'Content-Type': 'application/json;charset=UTF-8'},
            retries=2,
            component='kiwoom_token',
        )
        if not isinstance(data, dict):
            return ''
        token = str(data.get('token') or data.get('access_token') or '').strip()
        return token

    def _token_endpoint(self) -> str:
        return self.cfg.token_url or f'{self.cfg.base_url}{DEFAULT_TOKEN_PATH}'

    def _ohlcv_endpoint(self) -> str:
        return self.cfg.ohlcv_url or f'{self.cfg.base_url}{DEFAULT_OHLCV_PATH}'

    def _market_code(self, symbol: str) -> str:
        upper = symbol.strip().upper()
        if upper.endswith('.KS'):
            return '0'
        if upper.endswith('.KQ'):
            return '10'

        raw = str(self.cfg.market_type or '').strip().lower()
        if raw in {'kospi', '0'}:
            return '0'
        if raw in {'kosdaq', '10'}:
            return '10'
        for part in raw.split(','):
            part = part.strip()
            if part:
                return part
        return '0'

    def _query_date_token(self) -> str:
        raw = str(self.cfg.query_date or '').strip()
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if len(digits) == 8:
            return digits
        return datetime.now().strftime('%Y%m%d')

    def _post_json(
        self,
        url: str,
        payload: dict,
        headers: dict[str, str],
        *,
        retries: int = 2,
        component: str = 'kiwoom',
    ) -> dict | list | None:
        if not url:
            self._audit(component, 'url is empty')
            return None

        for attempt in range(1, retries + 1):
            req = Request(
                url=url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST',
            )
            try:
                with urlopen(req, timeout=15) as resp:  # noqa: S310
                    raw = resp.read().decode('utf-8')
                return json.loads(raw)
            except HTTPError as exc:
                try:
                    body = exc.read().decode('utf-8')
                except OSError:
                    body = str(exc)
                logger.warning('%s attempt=%d/%d status=%d body=%s', component, attempt, retries, exc.code, body[:400])
                self._audit(component, f'attempt={attempt}/{retries} status={exc.code} body={body[:400]}')
            except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
                logger.warning('%s attempt=%d/%d error=%s', component, attempt, retries, exc)
                self._audit(component, f'attempt={attempt}/{retries} error={exc}')
            if attempt < retries:
                time.sleep(0.7 * attempt)
        return None

    def _normalize_rows(self, data: dict | list | None) -> list[dict]:
        rows = self._extract_rows(data)
        out: list[dict] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            date_value = self._normalize_date(self._pick(row, self.ROW_FIELD_CANDIDATES['date']))
            close = self._as_float(self._pick(row, self.ROW_FIELD_CANDIDATES['close']))
            volume = self._as_float(self._pick(row, self.ROW_FIELD_CANDIDATES['volume']))
            if not date_value or close <= 0:
                continue
            out.append(
                {
                    'date': date_value,
                    'close': round(close, 2),
                    'volume': max(0, int(volume)),
                }
            )
        return self._merge_rows(out)

    def _extract_rows(self, data: dict | list | None) -> list:
        if data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in self.ENVELOPE_KEYS:
                value = data.get(key)
                if isinstance(value, list):
                    return value
                if isinstance(value, dict):
                    for nested_key in self.ENVELOPE_KEYS:
                        nested_value = value.get(nested_key)
                        if isinstance(nested_value, list):
                            return nested_value
        return []

    @staticmethod
    def _pick(row: dict, candidates: list[str]):
        for key in candidates:
            if key in row:
                return row[key]
        return None

    @staticmethod
    def _as_float(value) -> float:
        try:
            cleaned = str(value).replace(',', '').replace('+', '').strip()
            if not cleaned:
                return 0.0
            return abs(float(cleaned))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _normalize_date(value) -> str:
        raw = str(value or '').strip()
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if len(digits) == 8:
            return f'{digits[:4]}-{digits[4:6]}-{digits[6:8]}'
        return raw[:10] if raw else ''

    @staticmethod
    def _limit_rows(rows: list[dict], limit: int) -> list[dict]:
        if limit <= 0 or len(rows) <= limit:
            return list(rows)
        return list(rows[-limit:])

    def _cache_is_fresh(self, rows: list[dict], limit: int) -> bool:
        if not rows:
            return False
        latest_date = str(rows[-1].get('date', '')).strip()
        return len(rows) >= max(1, limit) and latest_date >= self._normalize_date(self._query_date_token())

    @staticmethod
    def _merge_rows(*sources: list[dict]) -> list[dict]:
        merged: dict[str, dict] = {}
        for rows in sources:
            for row in rows or []:
                date_value = str(row.get('date', '')).strip()
                close = row.get('close', 0.0)
                volume = row.get('volume', 0)
                if not date_value:
                    continue
                merged[date_value] = {
                    'date': date_value,
                    'close': round(float(close or 0.0), 2),
                    'volume': max(0, int(float(volume or 0.0))),
                }
        return [merged[key] for key in sorted(merged)]

    def _cache_path(self, symbol: str) -> Path:
        safe = symbol.replace('/', '_').replace('.', '_')
        return self.cache_dir / f'{safe}.json'

    def _read_cache(self, symbol: str) -> list[dict]:
        path = self._cache_path(symbol)
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return []
        if not isinstance(payload, list):
            return []
        return self._merge_rows(payload)

    def _write_cache(self, symbol: str, rows: list[dict]) -> None:
        path = self._cache_path(symbol)
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')

    def _audit(self, component: str, message: str) -> None:
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        path = self.audit_dir / f'{component}-{ts}.log'
        path.write_text(json.dumps({'timestamp': ts, 'message': message}, ensure_ascii=False), encoding='utf-8')
