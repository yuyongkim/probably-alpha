from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

from sepa.data.quantdb import read_company_snapshot

logger = logging.getLogger(__name__)


CACHE_DIR = Path('.omx/artifacts/market-data/company-facts')
CACHE_TTL = timedelta(hours=24)


def _cache_path(symbol: str) -> Path:
    return CACHE_DIR / f'{symbol}.json'


def _read_cache(symbol: str) -> dict | None:
    path = _cache_path(symbol)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return None

    fetched_at = payload.get('fetched_at')
    if not fetched_at:
        return None
    try:
        fetched = datetime.fromisoformat(str(fetched_at))
    except ValueError:
        return None
    if datetime.now() - fetched > CACHE_TTL:
        return None
    return payload


def _write_cache(symbol: str, payload: dict) -> dict:
    path = _cache_path(symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return payload


def _fast_info_value(fast_info, key: str):
    if fast_info is None:
        return None
    try:
        value = getattr(fast_info, key)
        if value is not None:
            return value
    except (AttributeError, TypeError, ValueError):
        pass
    try:
        return fast_info.get(key)
    except (AttributeError, TypeError):
        return None


def _estimate_shares_outstanding(mkt_cap, price) -> float | None:
    if not isinstance(mkt_cap, (int, float)) or not isinstance(price, (int, float)) or mkt_cap <= 0 or price <= 0:
        return None
    for scale in (
        100_000_000.0,
        10_000_000.0,
        1_000_000.0,
        100_000.0,
        10_000.0,
        1_000.0,
        100.0,
        10.0,
        1.0,
    ):
        shares = (float(mkt_cap) * scale) / float(price)
        if 1_000_000.0 <= shares <= 30_000_000_000.0:
            return float(shares)
    fallback = (float(mkt_cap) * 100_000_000.0) / float(price)
    return float(fallback) if fallback > 0 else None


def read_company_facts(symbol: str) -> dict:
    snapshot = read_company_snapshot(symbol)
    if snapshot:
        shares = snapshot.get('shares_outstanding') or _estimate_shares_outstanding(snapshot.get('mkt_cap'), snapshot.get('price'))
        latest_price = snapshot.get('price')
        estimated_cap = (float(shares) * float(latest_price)) if isinstance(shares, (int, float)) and isinstance(latest_price, (int, float)) and shares > 0 and latest_price > 0 else None
        # Preserve existing business_summary from cache if available
        cached = _read_cache(symbol)
        cached_summary = (cached.get('business_summary') or '') if cached else ''
        payload = {
            'symbol': symbol,
            'fetched_at': datetime.now().isoformat(timespec='seconds'),
            'shares_outstanding': int(shares) if isinstance(shares, (int, float)) and shares > 0 else None,
            'market_cap_latest': float(estimated_cap) if estimated_cap else None,
            'last_price_latest': float(latest_price) if isinstance(latest_price, (int, float)) and latest_price > 0 else None,
            'currency': 'KRW',
            'business_summary': cached_summary,
            'source': 'quantdb_snapshot',
        }
        return _write_cache(symbol, payload)

    cached = _read_cache(symbol)
    if cached is not None:
        return cached

    ticker = yf.Ticker(symbol)
    fast_info = None
    info = {}
    try:
        fast_info = ticker.fast_info
    except (ValueError, TypeError, KeyError, OSError) as exc:
        logger.debug('yfinance fast_info failed for %s: %s', symbol, exc)
        fast_info = None
    try:
        info = ticker.info if isinstance(ticker.info, dict) else {}
    except (ValueError, TypeError, KeyError, OSError) as exc:
        logger.debug('yfinance info failed for %s: %s', symbol, exc)
        info = {}

    shares_outstanding = info.get('sharesOutstanding') or info.get('impliedSharesOutstanding')
    market_cap_latest = _fast_info_value(fast_info, 'market_cap') or info.get('marketCap')
    last_price = _fast_info_value(fast_info, 'last_price') or info.get('currentPrice')
    currency = info.get('currency') or 'KRW'
    business_summary = str(info.get('longBusinessSummary') or '').strip()

    payload = {
        'symbol': symbol,
        'fetched_at': datetime.now().isoformat(timespec='seconds'),
        'shares_outstanding': int(shares_outstanding) if isinstance(shares_outstanding, (int, float)) and shares_outstanding > 0 else None,
        'market_cap_latest': float(market_cap_latest) if isinstance(market_cap_latest, (int, float)) and market_cap_latest > 0 else None,
        'last_price_latest': float(last_price) if isinstance(last_price, (int, float)) and last_price > 0 else None,
        'currency': currency,
        'business_summary': business_summary,
        'source': 'yfinance',
    }
    return _write_cache(symbol, payload)


def read_business_summary(symbol: str) -> str:
    """Return business summary. Priority: ohlcv.db description > cache > yfinance."""
    # Fast path: ohlcv.db description (from Naver)
    try:
        from sepa.data.ohlcv_db import get_symbol_meta
        meta = get_symbol_meta(symbol)
        if meta and meta.get('description'):
            return str(meta['description'])
    except Exception:
        pass

    cached = _read_cache(symbol)
    if cached is not None and cached.get('business_summary'):
        return str(cached['business_summary'])

    # If cache exists but has no summary, try yfinance directly
    if cached is not None and cached.get('source') == 'quantdb_snapshot':
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info if isinstance(ticker.info, dict) else {}
            summary = str(info.get('longBusinessSummary') or '').strip()
            if summary:
                cached['business_summary'] = summary
                _write_cache(symbol, cached)
                return summary
        except (ValueError, TypeError, KeyError, OSError) as exc:
            logger.debug('yfinance summary fetch failed for %s: %s', symbol, exc)
        # Fallback: generate from QuantDB sector info
        snapshot = read_company_snapshot(symbol)
        if snapshot:
            name = snapshot.get('name', symbol)
            sector_l = snapshot.get('sector_large', '')
            sector_s = snapshot.get('sector_small', '')
            market = snapshot.get('market', '')
            parts = [f'{name}']
            if market:
                parts.append(f'{market} 상장')
            if sector_s and sector_l and sector_s != sector_l:
                parts.append(f'{sector_l} > {sector_s} 업종')
            elif sector_l:
                parts.append(f'{sector_l} 업종')
            return ' | '.join(parts)
        return ''

    # No cache – generate a fast snippet from QuantDB and cache the facts
    # without blocking on yfinance (which can take 20+ seconds).
    snapshot = read_company_snapshot(symbol)
    if snapshot:
        name = snapshot.get('name', symbol)
        sector_l = snapshot.get('sector_large', '')
        sector_s = snapshot.get('sector_small', '')
        market = snapshot.get('market', '')
        parts = [f'{name}']
        if market:
            parts.append(f'{market} 상장')
        if sector_s and sector_l and sector_s != sector_l:
            parts.append(f'{sector_l} > {sector_s} 업종')
        elif sector_l:
            parts.append(f'{sector_l} 업종')
        snippet = ' | '.join(parts)
        # Populate the cache so subsequent calls are fast
        read_company_facts(symbol)
        return snippet
    # Last resort: trigger full yfinance fetch
    facts = read_company_facts(symbol)
    return str(facts.get('business_summary') or '')


def estimated_market_cap(symbol: str, close_price: float | None) -> dict:
    facts = read_company_facts(symbol)
    shares = facts.get('shares_outstanding')
    close = float(close_price) if isinstance(close_price, (int, float)) else None
    estimated = (close * shares) if close and shares else None
    return {
        **facts,
        'market_cap_estimated': float(estimated) if estimated else None,
        'market_cap_basis': 'close x current shares outstanding',
    }
