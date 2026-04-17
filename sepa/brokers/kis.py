from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


KIS_PROD_BASE_URL = 'https://openapi.koreainvestment.com:9443'
KIS_DEMO_BASE_URL = 'https://openapivts.koreainvestment.com:29443'
KIS_TOKEN_PATH = '/oauth2/tokenP'
KIS_HASHKEY_PATH = '/uapi/hashkey'
_TOKEN_CACHE: dict[str, dict[str, Any]] = {}


class KisApiError(RuntimeError):
    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.payload = payload or {}


@dataclass(frozen=True)
class KisConfig:
    app_key: str
    app_secret: str
    account_no: str
    account_product_code: str
    env: str
    base_url: str
    order_enabled: bool


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in {'1', 'true', 'yes', 'on'}


def _normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if value.startswith('A') and len(value) >= 7 and value[1:7].isdigit():
        return value[1:7]
    if '.' in value:
        left = value.split('.', 1)[0]
        if left.isdigit():
            return left
    return value


def _to_int(value: Any) -> int | None:
    raw = str(value or '').replace(',', '').replace('+', '').strip()
    if not raw or raw in {'-', 'None'}:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def _to_float(value: Any) -> float | None:
    raw = str(value or '').replace(',', '').replace('+', '').strip()
    if not raw or raw in {'-', 'None'}:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


class KisBroker:
    def __init__(self, config: KisConfig) -> None:
        self.config = config
        self._access_token = ''
        self._access_token_expires_at = 0.0

    @classmethod
    def from_env(cls) -> 'KisBroker':
        raw_env = os.getenv('KIS_ENV', 'prod').strip().lower()
        normalized_env = 'demo' if raw_env in {'demo', 'paper', 'vps'} else 'prod'
        default_base = KIS_DEMO_BASE_URL if normalized_env == 'demo' else KIS_PROD_BASE_URL
        return cls(
            KisConfig(
                app_key=os.getenv('KIS_APP_KEY', '').strip(),
                app_secret=os.getenv('KIS_APP_SECRET', '').strip(),
                account_no=os.getenv('KIS_ACCOUNT_NO', '').strip(),
                account_product_code=os.getenv('KIS_ACCOUNT_PRODUCT_CODE', '').strip(),
                env=normalized_env,
                base_url=os.getenv('KIS_BASE_URL', default_base).strip().rstrip('/') or default_base,
                order_enabled=_truthy(os.getenv('SEPA_KIS_ORDER_ENABLED', '0')),
            )
        )

    def has_credentials(self) -> bool:
        return bool(self.config.app_key and self.config.app_secret)

    def has_account(self) -> bool:
        return bool(self.config.account_no and self.config.account_product_code)

    def health(self, *, check_auth: bool = True) -> dict:
        payload = {
            'env': self.config.env,
            'base_url': self.config.base_url,
            'has_app_key': bool(self.config.app_key),
            'has_app_secret': bool(self.config.app_secret),
            'has_account_no': bool(self.config.account_no),
            'has_account_product_code': bool(self.config.account_product_code),
            'order_enabled': self.config.order_enabled,
            'auth_ok': False,
        }
        if not check_auth or not self.has_credentials():
            return payload
        try:
            token_payload = self.issue_token()
            payload.update(
                {
                    'auth_ok': True,
                    'access_token_expires_at': token_payload.get('access_token_token_expired'),
                    'expires_in': token_payload.get('expires_in'),
                }
            )
        except KisApiError as exc:
            payload.update(
                {
                    'auth_ok': False,
                    'error_code': exc.code,
                    'error_message': str(exc),
                }
            )
        return payload

    def issue_token(self, *, force: bool = False) -> dict[str, Any]:
        now = time.time()
        cache_key = self._token_cache_key()
        cached = _TOKEN_CACHE.get(cache_key)
        if not force and cached and now < float(cached.get('expires_at', 0.0)) - 60:
            self._access_token = str(cached.get('access_token') or '')
            self._access_token_expires_at = float(cached.get('expires_at') or 0.0)
            return {
                'access_token': self._access_token,
                'expires_in': int(self._access_token_expires_at - now),
                'access_token_token_expired': str(cached.get('access_token_token_expired') or ''),
            }
        if not force and self._access_token and now < self._access_token_expires_at - 60:
            return {
                'access_token': self._access_token,
                'expires_in': int(self._access_token_expires_at - now),
                'access_token_token_expired': datetime.fromtimestamp(self._access_token_expires_at).strftime('%Y-%m-%d %H:%M:%S'),
            }

        if not self.has_credentials():
            raise KisApiError(503, 'KIS credentials are not configured')

        payload = self._request_json(
            'POST',
            KIS_TOKEN_PATH,
            headers={'content-type': 'application/json'},
            body={
                'grant_type': 'client_credentials',
                'appkey': self.config.app_key,
                'appsecret': self.config.app_secret,
            },
        )
        token = str(payload.get('access_token') or '').strip()
        if not token:
            raise KisApiError(502, 'KIS token response missing access_token', payload=payload)

        expires_in = int(payload.get('expires_in') or 0) or 3600
        self._access_token = token
        self._access_token_expires_at = now + max(60, expires_in)
        _TOKEN_CACHE[cache_key] = {
            'access_token': token,
            'expires_at': self._access_token_expires_at,
            'access_token_token_expired': str(payload.get('access_token_token_expired') or ''),
        }
        return payload

    def etf_quote(self, symbol: str, *, market_div: str = 'J') -> dict:
        pdno = _normalize_symbol(symbol)
        payload = self._request_json(
            'GET',
            '/uapi/etfetn/v1/quotations/inquire-price',
            headers=self._auth_headers('FHPST02400000'),
            params={
                'FID_COND_MRKT_DIV_CODE': market_div,
                'FID_INPUT_ISCD': pdno,
            },
        )
        output = payload.get('output') or {}
        name = (
            str(output.get('hts_kor_isnm') or output.get('bstp_kor_isnm') or output.get('prdt_name') or pdno).strip()
            or pdno
        )
        return {
            'symbol': pdno,
            'name': name,
            'current_price': _to_int(output.get('stck_prpr')),
            'change': _to_int(output.get('prdy_vrss')),
            'change_sign': str(output.get('prdy_vrss_sign') or '').strip(),
            'change_pct': _to_float(output.get('prdy_ctrt')),
            'open': _to_int(output.get('stck_oprc')),
            'high': _to_int(output.get('stck_hgpr')),
            'low': _to_int(output.get('stck_lwpr')),
            'prev_close': _to_int(output.get('stck_prdy_clpr')),
            'volume': _to_int(output.get('acml_vol')),
            'prev_volume': _to_int(output.get('prdy_vol')),
            'trade_value': _to_int(output.get('acml_tr_pbmn')),
            'upper_limit': _to_int(output.get('stck_mxpr')),
            'lower_limit': _to_int(output.get('stck_llam')),
            'raw': output,
        }

    def daily_chart(
        self,
        symbol: str,
        *,
        date_from: str,
        date_to: str,
        market_div: str = 'J',
        period_div: str = 'D',
        adjusted_price: bool = True,
    ) -> dict:
        pdno = _normalize_symbol(symbol)
        payload = self._request_json(
            'GET',
            '/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice',
            headers=self._auth_headers('FHKST03010100'),
            params={
                'FID_COND_MRKT_DIV_CODE': market_div,
                'FID_INPUT_ISCD': pdno,
                'FID_INPUT_DATE_1': date_from,
                'FID_INPUT_DATE_2': date_to,
                'FID_PERIOD_DIV_CODE': period_div,
                'FID_ORG_ADJ_PRC': '1' if adjusted_price else '0',
            },
        )
        meta = payload.get('output1') or {}
        rows = payload.get('output2') or []
        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            trade_date = str(row.get('stck_bsop_date') or '').strip()
            if len(trade_date) != 8:
                continue
            normalized_rows.append(
                {
                    'date': f'{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}',
                    'open': _to_int(row.get('stck_oprc')),
                    'high': _to_int(row.get('stck_hgpr')),
                    'low': _to_int(row.get('stck_lwpr')),
                    'close': _to_int(row.get('stck_clpr')),
                    'volume': _to_int(row.get('acml_vol')),
                    'trade_value': _to_int(row.get('acml_tr_pbmn')),
                }
            )
        normalized_rows.sort(key=lambda item: item['date'])
        return {
            'symbol': pdno,
            'name': str(meta.get('hts_kor_isnm') or pdno).strip(),
            'current_price': _to_int(meta.get('stck_prpr')),
            'date_from': date_from,
            'date_to': date_to,
            'rows': normalized_rows,
            'raw_meta': meta,
        }

    def overseas_price(
        self,
        symbol: str,
        *,
        exchange_code: str,
        auth: str = '',
    ) -> dict:
        payload = self._request_json(
            'GET',
            '/uapi/overseas-price/v1/quotations/price',
            headers=self._auth_headers('HHDFS00000300'),
            params={
                'AUTH': auth,
                'EXCD': exchange_code,
                'SYMB': symbol.strip().upper(),
            },
        )
        output = payload.get('output') or {}
        return {
            'symbol': symbol.strip().upper(),
            'exchange_code': exchange_code,
            'last': _to_float(output.get('last')),
            'base': _to_float(output.get('base')),
            'change': _to_float(output.get('diff')),
            'change_pct': _to_float(output.get('rate')),
            'volume': _to_int(output.get('tvol')),
            'prev_volume': _to_int(output.get('pvol')),
            'trade_value': _to_float(output.get('tamt')),
            'currency_hint': str(output.get('curr') or '').strip(),
            'raw': output,
        }

    def overseas_price_detail(
        self,
        symbol: str,
        *,
        exchange_code: str,
        auth: str = '',
    ) -> dict:
        payload = self._request_json(
            'GET',
            '/uapi/overseas-price/v1/quotations/price-detail',
            headers=self._auth_headers('HHDFS76200200'),
            params={
                'AUTH': auth,
                'EXCD': exchange_code,
                'SYMB': symbol.strip().upper(),
            },
        )
        output = payload.get('output') or {}
        return {
            'symbol': symbol.strip().upper(),
            'exchange_code': exchange_code,
            'currency': str(output.get('curr') or '').strip() or None,
            'open': _to_float(output.get('open')),
            'high': _to_float(output.get('high')),
            'low': _to_float(output.get('low')),
            'last': _to_float(output.get('last')),
            'base': _to_float(output.get('base')),
            'high_52w': _to_float(output.get('h52p')),
            'high_52w_date': str(output.get('h52d') or '').strip() or None,
            'low_52w': _to_float(output.get('l52p')),
            'low_52w_date': str(output.get('l52d') or '').strip() or None,
            'per': _to_float(output.get('perx')),
            'pbr': _to_float(output.get('pbrx')),
            'eps': _to_float(output.get('epsx')),
            'shares_listed': _to_int(output.get('shar')),
            'raw': output,
        }

    def overseas_search_info(
        self,
        symbol: str,
        *,
        product_type_code: str = '512',
    ) -> dict:
        payload = self._request_json(
            'GET',
            '/uapi/overseas-price/v1/quotations/search-info',
            headers=self._auth_headers('CTPF1702R'),
            params={
                'PRDT_TYPE_CD': product_type_code,
                'PDNO': symbol.strip().upper(),
            },
        )
        output = payload.get('output') or {}
        return {
            'symbol': symbol.strip().upper(),
            'product_type_code': product_type_code,
            'isin': str(output.get('std_pdno') or '').strip() or None,
            'name': str(output.get('prdt_eng_name') or '').strip() or symbol.strip().upper(),
            'country_code': str(output.get('natn_cd') or '').strip() or None,
            'country_name': str(output.get('natn_name') or '').strip() or None,
            'market_name': str(output.get('tr_mket_name') or output.get('ovrs_excg_name') or '').strip() or None,
            'exchange_code': str(output.get('ovrs_excg_cd') or '').strip() or None,
            'currency': str(output.get('tr_crcy_cd') or '').strip() or None,
            'product_class_name': str(output.get('prdt_clsf_name') or '').strip() or None,
            'listed_shares': _to_int(output.get('lstg_stck_num')),
            'raw': output,
        }

    def overseas_daily_chart(
        self,
        symbol: str,
        *,
        exchange_code: str,
        auth: str = '',
        price_basis: str = '0',
        adjusted_price: str = '1',
    ) -> dict:
        payload = self._request_json(
            'GET',
            '/uapi/overseas-price/v1/quotations/dailyprice',
            headers=self._auth_headers('HHDFS76240000'),
            params={
                'AUTH': auth,
                'EXCD': exchange_code,
                'SYMB': symbol.strip().upper(),
                'GUBN': price_basis,
                'BYMD': '',
                'MODP': adjusted_price,
            },
        )
        meta = payload.get('output1') or {}
        rows = payload.get('output2') or []
        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            trade_date = str(row.get('xymd') or '').strip()
            if len(trade_date) != 8:
                continue
            normalized_rows.append(
                {
                    'date': f'{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}',
                    'open': _to_float(row.get('open')),
                    'high': _to_float(row.get('high')),
                    'low': _to_float(row.get('low')),
                    'close': _to_float(row.get('clos')),
                    'volume': _to_int(row.get('tvol')),
                    'trade_value': _to_float(row.get('tamt')),
                }
            )
        normalized_rows = [row for row in normalized_rows if row.get('close')]
        normalized_rows.sort(key=lambda item: item['date'])
        return {
            'symbol': symbol.strip().upper(),
            'exchange_code': exchange_code,
            'record_count': _to_int(meta.get('nrec')),
            'rows': normalized_rows,
            'raw_meta': meta,
        }

    def order_preview(
        self,
        symbol: str,
        *,
        order_price: float,
        order_type: str = '00',
        include_cma: str = 'N',
        include_overseas: str = 'N',
    ) -> dict:
        self._require_account()
        tr_id = 'VTTC8908R' if self.config.env == 'demo' else 'TTTC8908R'
        payload = self._request_json(
            'GET',
            '/uapi/domestic-stock/v1/trading/inquire-psbl-order',
            headers=self._auth_headers(tr_id),
            params={
                'CANO': self.config.account_no,
                'ACNT_PRDT_CD': self.config.account_product_code,
                'PDNO': _normalize_symbol(symbol),
                'ORD_UNPR': str(int(round(order_price))),
                'ORD_DVSN': order_type,
                'CMA_EVLU_AMT_ICLD_YN': include_cma,
                'OVRS_ICLD_YN': include_overseas,
            },
        )
        output = payload.get('output') or {}
        return {
            'symbol': _normalize_symbol(symbol),
            'order_price': int(round(order_price)),
            'cash_available': _to_int(output.get('ord_psbl_cash')),
            'max_buy_amount': _to_int(output.get('max_buy_amt')),
            'max_buy_qty': _to_int(output.get('max_buy_qty')),
            'cash_only_buy_amount': _to_int(output.get('nrcvb_buy_amt')),
            'cash_only_buy_qty': _to_int(output.get('nrcvb_buy_qty')),
            'raw': output,
        }

    def order_cash(
        self,
        symbol: str,
        *,
        side: str,
        quantity: int,
        order_price: float,
        order_type: str = '00',
        exchange_code: str = 'KRX',
        sell_type: str = '',
        condition_price: str = '',
    ) -> dict:
        self._require_account()
        if not self.config.order_enabled:
            raise KisApiError(403, 'KIS live order route is disabled; set SEPA_KIS_ORDER_ENABLED=1 to enable')

        normalized_side = side.strip().lower()
        if normalized_side not in {'buy', 'sell'}:
            raise KisApiError(400, 'side must be buy or sell')

        tr_id_map = {
            ('prod', 'buy'): 'TTTC0012U',
            ('prod', 'sell'): 'TTTC0011U',
            ('demo', 'buy'): 'VTTC0012U',
            ('demo', 'sell'): 'VTTC0011U',
        }
        tr_id = tr_id_map[(self.config.env, normalized_side)]
        body = {
            'CANO': self.config.account_no,
            'ACNT_PRDT_CD': self.config.account_product_code,
            'PDNO': _normalize_symbol(symbol),
            'ORD_DVSN': order_type,
            'ORD_QTY': str(int(quantity)),
            'ORD_UNPR': str(int(round(order_price))),
            'EXCG_ID_DVSN_CD': exchange_code,
            'SLL_TYPE': sell_type,
            'CNDT_PRIC': condition_price,
        }
        headers = self._auth_headers(tr_id)
        hashkey = self._create_hashkey(body)
        if hashkey:
            headers['hashkey'] = hashkey

        payload = self._request_json(
            'POST',
            '/uapi/domestic-stock/v1/trading/order-cash',
            headers=headers,
            body=body,
        )
        output = payload.get('output') or {}
        return {
            'symbol': _normalize_symbol(symbol),
            'side': normalized_side,
            'quantity': int(quantity),
            'order_price': int(round(order_price)),
            'order_no': str(output.get('ODNO') or output.get('odno') or '').strip(),
            'order_time': str(output.get('ORD_TMD') or output.get('ord_tmd') or '').strip(),
            'raw': output,
            'hashkey_applied': bool(hashkey),
        }

    def _create_hashkey(self, body: dict[str, Any]) -> str:
        try:
            payload = self._request_json(
                'POST',
                KIS_HASHKEY_PATH,
                headers={
                    'content-type': 'application/json',
                    'appkey': self.config.app_key,
                    'appsecret': self.config.app_secret,
                },
                body=body,
            )
        except KisApiError:
            return ''
        return str(payload.get('HASH') or '').strip()

    def _require_account(self) -> None:
        if not self.has_account():
            raise KisApiError(503, 'KIS account information is not configured')

    def _auth_headers(self, tr_id: str) -> dict[str, str]:
        token_payload = self.issue_token()
        token = str(token_payload.get('access_token') or self._access_token).strip()
        return {
            'content-type': 'application/json',
            'authorization': f'Bearer {token}',
            'appkey': self.config.app_key,
            'appsecret': self.config.app_secret,
            'custtype': 'P',
            'tr_id': tr_id,
        }

    def _token_cache_key(self) -> str:
        return f'{self.config.env}:{self.config.app_key}'

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f'{self.config.base_url}{path}'
        if params:
            query = urlencode({key: value for key, value in params.items() if value is not None})
            url = f'{url}?{query}'
        data = json.dumps(body).encode('utf-8') if body is not None else None
        request = Request(url=url, data=data, headers=headers, method=method.upper())
        try:
            with urlopen(request, timeout=20) as response:  # noqa: S310
                raw = response.read().decode('utf-8')
                payload = json.loads(raw)
        except HTTPError as exc:
            raise self._build_api_error(exc.code, exc.read().decode('utf-8', errors='ignore')) from exc
        except URLError as exc:
            raise KisApiError(503, f'KIS network error: {exc}') from exc
        except json.JSONDecodeError as exc:
            raise KisApiError(502, 'KIS returned invalid JSON') from exc

        if isinstance(payload, dict) and payload.get('rt_cd') not in {None, '0'}:
            raise KisApiError(
                502,
                str(payload.get('msg1') or 'KIS request failed'),
                code=str(payload.get('msg_cd') or ''),
                payload=payload,
            )
        return payload

    @staticmethod
    def _build_api_error(status_code: int, raw_body: str) -> KisApiError:
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            payload = {}
        if payload:
            return KisApiError(
                status_code,
                str(payload.get('msg1') or payload.get('error_description') or raw_body[:240] or 'KIS request failed'),
                code=str(payload.get('msg_cd') or payload.get('error') or ''),
                payload=payload,
            )
        return KisApiError(status_code, raw_body[:240] or 'KIS request failed')
