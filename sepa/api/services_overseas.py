from __future__ import annotations

import time
from statistics import mean, pstdev

from sepa.analysis.patterns import detect_support_resistance
from sepa.brokers import KisApiError, KisBroker


def _price_metrics(rows: list[dict]) -> dict:
    closes = [float(row.get('close', 0.0) or 0.0) for row in rows if row.get('close')]
    if not closes:
        return {
            'sma20': None,
            'sma60': None,
            'return_20d_pct': None,
            'return_60d_pct': None,
            'volatility_20d_pct': None,
            'trend_state': 'unknown',
        }

    sma20 = mean(closes[-20:]) if len(closes) >= 20 else mean(closes)
    sma60 = mean(closes[-60:]) if len(closes) >= 60 else mean(closes)
    return_20d = ((closes[-1] / closes[-21]) - 1.0) * 100.0 if len(closes) >= 21 and closes[-21] > 0 else None
    return_60d = ((closes[-1] / closes[-61]) - 1.0) * 100.0 if len(closes) >= 61 and closes[-61] > 0 else None

    returns = []
    for idx in range(max(1, len(closes) - 20), len(closes)):
        prev = closes[idx - 1]
        curr = closes[idx]
        if prev > 0:
            returns.append(curr / prev - 1.0)
    volatility_20d = pstdev(returns) * 100.0 if len(returns) >= 2 else None

    current = closes[-1]
    if current > sma20 > sma60:
        trend_state = 'strong_uptrend'
    elif current > sma20:
        trend_state = 'uptrend'
    elif current > sma60:
        trend_state = 'range_above_medium_trend'
    else:
        trend_state = 'weak_or_downtrend'

    return {
        'sma20': round(sma20, 2),
        'sma60': round(sma60, 2),
        'return_20d_pct': round(return_20d, 2) if return_20d is not None else None,
        'return_60d_pct': round(return_60d, 2) if return_60d is not None else None,
        'volatility_20d_pct': round(volatility_20d, 2) if volatility_20d is not None else None,
        'trend_state': trend_state,
    }


def _call_with_retry(func, *args, retries: int = 3, base_sleep_sec: float = 0.45, **kwargs):
    for attempt in range(1, retries + 1):
        try:
            return func(*args, **kwargs)
        except KisApiError as exc:
            message = str(exc)
            is_rate_limited = '초당 거래건수' in message or '잠시 후 다시 시도' in message
            if not is_rate_limited or attempt == retries:
                raise
            time.sleep(base_sleep_sec * attempt)


def overseas_stock_analysis_payload(
    symbol: str,
    *,
    exchange_code: str = 'NAS',
    product_type_code: str = '512',
) -> dict:
    broker = KisBroker.from_env()
    if not broker.has_credentials():
        return {
            'symbol': symbol,
            'error': 'missing_kis_credentials',
            'message': 'KIS_APP_KEY and KIS_APP_SECRET are required',
        }

    normalized_symbol = symbol.strip().upper()
    normalized_exchange = exchange_code.strip().upper()
    normalized_product_type = product_type_code.strip()

    quote = _call_with_retry(broker.overseas_price, normalized_symbol, exchange_code=normalized_exchange)
    time.sleep(0.18)
    detail = _call_with_retry(broker.overseas_price_detail, normalized_symbol, exchange_code=normalized_exchange)
    time.sleep(0.18)
    info = _call_with_retry(broker.overseas_search_info, normalized_symbol, product_type_code=normalized_product_type)
    time.sleep(0.18)
    chart = _call_with_retry(broker.overseas_daily_chart, normalized_symbol, exchange_code=normalized_exchange)

    levels = detect_support_resistance(chart.get('rows', []), lookback=100, order=4, tolerance_pct=1.5, max_levels=3)
    metrics = _price_metrics(chart.get('rows', []))
    current_price = quote.get('last') or detail.get('last')
    nearest_support = (levels.get('nearest_support') or {}).get('price')
    nearest_resistance = (levels.get('nearest_resistance') or {}).get('price')
    trade_levels = {
        'breakout_entry': round((nearest_resistance or current_price or 0.0) * 1.002, 2) if (nearest_resistance or current_price) else None,
        'pullback_entry': round((nearest_support or current_price or 0.0) * 1.003, 2) if (nearest_support or current_price) else None,
        'stop_price': round((nearest_support or (current_price or 0.0) * 0.97) * 0.985, 2) if current_price else None,
    }

    return {
        'symbol': normalized_symbol,
        'name': info.get('name') or normalized_symbol,
        'exchange_code': normalized_exchange,
        'product_type_code': normalized_product_type,
        'quote': quote,
        'detail': detail,
        'info': info,
        'chart': chart.get('rows', []),
        'support_resistance': levels,
        'metrics': metrics,
        'trade_levels': trade_levels,
        'disclaimer': '해외주식 분석은 KIS 조회 응답 기반 참고 정보이며 투자 권유가 아닙니다.',
    }
