from __future__ import annotations

from datetime import datetime, timedelta
from statistics import mean, pstdev

from sepa.analysis.patterns import detect_support_resistance
from sepa.brokers import KisApiError, KisBroker


SUPPORTED_RISK_PROFILES = {'conservative', 'balanced', 'aggressive'}


def _normalize_date_token(value: str | None, fallback: datetime) -> str:
    raw = ''.join(ch for ch in str(value or '').strip() if ch.isdigit())
    if len(raw) == 8:
        return raw
    return fallback.strftime('%Y%m%d')


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


def _heuristic_trade_levels(current_price: float | None, levels: dict) -> dict:
    if not current_price:
        return {
            'breakout_entry': None,
            'pullback_entry': None,
            'stop_price': None,
            'target_price': None,
            'rr_ratio': None,
        }

    nearest_support = levels.get('nearest_support') or {}
    nearest_resistance = levels.get('nearest_resistance') or {}
    breakout_entry = round((nearest_resistance.get('price') or current_price) * 1.002, 2)
    pullback_entry = round((nearest_support.get('price') or current_price) * 1.003, 2)
    stop_price = round((nearest_support.get('price') or current_price * 0.97) * 0.985, 2)
    target_anchor = nearest_resistance.get('price') if nearest_resistance else current_price * 1.05
    target_price = round(max(target_anchor, breakout_entry) * 1.03, 2)
    risk = max(0.01, breakout_entry - stop_price)
    rr_ratio = round((target_price - breakout_entry) / risk, 2) if risk > 0 else None
    return {
        'breakout_entry': breakout_entry,
        'pullback_entry': pullback_entry,
        'stop_price': stop_price,
        'target_price': target_price,
        'rr_ratio': rr_ratio,
    }


def _profile_score(profile: str, analysis: dict) -> tuple[float, list[str]]:
    metrics = analysis.get('metrics') or {}
    levels = analysis.get('support_resistance') or {}
    quote = analysis.get('quote') or {}
    current_price = float(quote.get('current_price') or 0.0)
    nearest_support = (levels.get('nearest_support') or {}).get('distance_pct')
    nearest_resistance = (levels.get('nearest_resistance') or {}).get('distance_pct')

    trend_score = {
        'strong_uptrend': 100.0,
        'uptrend': 82.0,
        'range_above_medium_trend': 58.0,
        'weak_or_downtrend': 18.0,
        'unknown': 10.0,
    }.get(metrics.get('trend_state', 'unknown'), 10.0)
    support_score = max(0.0, 100.0 - min(100.0, float(nearest_support or 12.0) * 8.0))
    room_score = min(100.0, max(0.0, float(nearest_resistance or 0.0) * 9.0))
    volatility = float(metrics.get('volatility_20d_pct') or 0.0)
    low_vol_score = max(0.0, 100.0 - min(100.0, volatility * 10.0))
    momentum = max(
        0.0,
        min(
            100.0,
            50.0
            + float(metrics.get('return_20d_pct') or 0.0) * 2.0
            + float(metrics.get('return_60d_pct') or 0.0) * 1.2,
        ),
    )

    if profile == 'conservative':
        score = trend_score * 0.30 + support_score * 0.25 + low_vol_score * 0.25 + room_score * 0.10 + momentum * 0.10
        reasons = [
            '변동성이 낮고 지지선이 가까운 ETF를 우선',
            '중기 추세가 살아 있는지 가중치 높게 반영',
        ]
    elif profile == 'aggressive':
        score = trend_score * 0.15 + support_score * 0.10 + low_vol_score * 0.10 + room_score * 0.25 + momentum * 0.40
        reasons = [
            '20일/60일 모멘텀과 돌파 여지를 가장 크게 반영',
            '단기 변동성은 감수하는 대신 추세 지속성에 가중치',
        ]
    else:
        score = trend_score * 0.25 + support_score * 0.20 + low_vol_score * 0.15 + room_score * 0.20 + momentum * 0.20
        reasons = [
            '추세, 지지선 근접도, 저항선까지의 여지를 균형 있게 반영',
            '모멘텀은 보되 과도한 변동성은 감점',
        ]

    if current_price <= 0:
        score = 0.0
        reasons = ['현재가를 확인할 수 없어 점수를 0으로 처리']

    return round(score, 2), reasons


def kis_health_payload() -> dict:
    broker = KisBroker.from_env()
    return broker.health(check_auth=True)


def etf_analysis_payload(symbol: str, *, date_from: str | None = None, date_to: str | None = None) -> dict:
    broker = KisBroker.from_env()
    if not broker.has_credentials():
        return {
            'symbol': symbol,
            'error': 'missing_kis_credentials',
            'message': 'KIS_APP_KEY and KIS_APP_SECRET are required',
        }

    today = datetime.now()
    resolved_to = _normalize_date_token(date_to, today)
    resolved_from = _normalize_date_token(date_from, today - timedelta(days=180))

    quote = broker.etf_quote(symbol)
    chart = broker.daily_chart(symbol, date_from=resolved_from, date_to=resolved_to)
    resolved_name = quote.get('name') or chart.get('name') or symbol
    if quote.get('name') == quote.get('symbol'):
        resolved_name = chart.get('name') or quote.get('name') or symbol
    levels = detect_support_resistance(chart.get('rows', []))
    metrics = _price_metrics(chart.get('rows', []))
    trade_levels = _heuristic_trade_levels(float(quote.get('current_price') or 0.0), levels)

    return {
        'symbol': quote.get('symbol') or symbol,
        'name': resolved_name,
        'date_from': resolved_from,
        'date_to': resolved_to,
        'quote': quote,
        'chart': chart.get('rows', []),
        'support_resistance': levels,
        'metrics': metrics,
        'trade_levels': trade_levels,
        'disclaimer': '이 화면의 점수와 레벨은 휴리스틱 참고용이며 투자 권유가 아닙니다.',
    }


def etf_profile_recommendations_payload(
    symbols: list[str],
    *,
    risk_profile: str = 'balanced',
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    normalized_profile = risk_profile.strip().lower()
    if normalized_profile not in SUPPORTED_RISK_PROFILES:
        raise ValueError(f'unsupported risk_profile: {risk_profile}')

    unique_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        normalized = symbol.strip().upper()
        if not normalized or normalized in seen:
            continue
        unique_symbols.append(normalized)
        seen.add(normalized)

    items = []
    for symbol in unique_symbols[:20]:
        try:
            analysis = etf_analysis_payload(symbol, date_from=date_from, date_to=date_to)
            if analysis.get('error'):
                items.append({'symbol': symbol, 'error': analysis.get('error'), 'message': analysis.get('message')})
                continue
            score, reasons = _profile_score(normalized_profile, analysis)
            items.append(
                {
                    'symbol': analysis.get('symbol'),
                    'name': analysis.get('name'),
                    'score': score,
                    'risk_profile': normalized_profile,
                    'reasons': reasons,
                    'quote': analysis.get('quote'),
                    'metrics': analysis.get('metrics'),
                    'support_resistance': analysis.get('support_resistance'),
                    'trade_levels': analysis.get('trade_levels'),
                }
            )
        except KisApiError as exc:
            items.append({'symbol': symbol, 'error': 'kis_api_error', 'message': str(exc), 'status_code': exc.status_code})

    ranked = sorted(
        [item for item in items if 'score' in item],
        key=lambda item: item['score'],
        reverse=True,
    )
    failures = [item for item in items if 'score' not in item]
    return {
        'risk_profile': normalized_profile,
        'count': len(ranked),
        'items': ranked,
        'failures': failures,
        'disclaimer': '프로파일별 점수는 선택한 ETF 후보군 내부 상대평가이며, 최종 투자판단은 별도로 필요합니다.',
    }


def kis_order_preview_payload(
    symbol: str,
    *,
    order_price: float,
    order_type: str = '00',
    include_cma: str = 'N',
    include_overseas: str = 'N',
) -> dict:
    broker = KisBroker.from_env()
    quote = broker.etf_quote(symbol)
    preview = broker.order_preview(
        symbol,
        order_price=order_price,
        order_type=order_type,
        include_cma=include_cma,
        include_overseas=include_overseas,
    )
    return {
        'symbol': preview.get('symbol'),
        'quote': quote,
        'preview': preview,
    }


def kis_order_cash_payload(
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
    broker = KisBroker.from_env()
    quote = broker.etf_quote(symbol)
    order = broker.order_cash(
        symbol,
        side=side,
        quantity=quantity,
        order_price=order_price,
        order_type=order_type,
        exchange_code=exchange_code,
        sell_type=sell_type,
        condition_price=condition_price,
    )
    return {
        'symbol': order.get('symbol'),
        'quote': quote,
        'order': order,
    }
