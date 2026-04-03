from __future__ import annotations

from collections import Counter
from functools import lru_cache
from statistics import mean, pstdev

from sepa.data.company_facts import estimated_market_cap
from sepa.data.fundamentals import read_eps_series
from sepa.data.market_index import read_market_index_series
from sepa.data.price_history import read_price_series
from sepa.data.sector_map import get_sector, load_sector_map
from sepa.data.symbols import infer_market
from sepa.data.universe import get_symbol_name, load_symbols

# ---------------------------------------------------------------------------
# Re-exports from indicators and patterns for backward compatibility.
# All existing ``from sepa.analysis.stock_analysis import X`` statements
# will continue to work unchanged.
# ---------------------------------------------------------------------------
from sepa.analysis.indicators import (  # noqa: F401 — re-exports
    _rebase_base100,
    _round_or_none,
    _round_series,
    _to_num,
    ema,
    linear_regression_slope_intercept,
    macd,
    moving_average,
    moving_average_nullable,
)
from sepa.analysis.patterns import detect_cup_with_handle  # noqa: F401 — re-export


SECTOR_MAP = load_sector_map()


# ---------------------------------------------------------------------------
# Least resistance
# ---------------------------------------------------------------------------

def least_resistance(price_series: list[dict], window: int = 50) -> dict:
    closes = [row['close'] for row in price_series if row.get('close')]
    if len(closes) < max(20, window):
        return {'trend': 'unknown', 'slope': 0.0, 'distance_pct': 0.0, 'line_last': 0.0}

    part = closes[-window:]
    slope, intercept = linear_regression_slope_intercept(part)
    line_last = slope * (len(part) - 1) + intercept
    current = part[-1]
    distance_pct = ((current - line_last) / line_last * 100.0) if line_last else 0.0

    if slope > 0 and distance_pct >= 0:
        trend = 'up_least_resistance'
    elif slope > 0:
        trend = 'pullback_in_uptrend'
    elif slope < 0 and distance_pct < 0:
        trend = 'downtrend'
    else:
        trend = 'sideways'

    return {
        'trend': trend,
        'slope': round(slope, 6),
        'line_last': round(line_last, 3),
        'distance_pct': round(distance_pct, 2),
    }


def least_resistance_line(price_series: list[dict], window: int = 50) -> list[float | None]:
    closes = [row['close'] for row in price_series if row.get('close')]
    size = len(closes)
    if size < max(20, window):
        return [None] * size

    part = closes[-window:]
    slope, intercept = linear_regression_slope_intercept(part)
    line = [None] * (size - window)
    for idx in range(window):
        line.append(round((slope * idx) + intercept, 3))
    return line


# ---------------------------------------------------------------------------
# Market-wide data (heavy O(N-symbols) functions)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=16)
def _ret120_percentile_map(as_of_date: str | None = None) -> dict[str, float]:
    out: dict[str, float] = {}
    values: list[tuple[str, float]] = []
    for symbol in load_symbols():
        series = read_price_series(symbol, as_of_date=as_of_date)
        closes = [row.get('close', 0.0) for row in series if row.get('close', 0.0) > 0]
        if len(closes) < 121:
            continue
        base = closes[-121]
        if base <= 0:
            continue
        values.append((symbol, closes[-1] / base - 1.0))

    ranked = sorted(values, key=lambda item: item[1])
    if not ranked:
        return out
    if len(ranked) == 1:
        return {ranked[0][0]: 100.0}
    for idx, (symbol, _) in enumerate(ranked):
        out[symbol] = (idx / (len(ranked) - 1)) * 100.0
    return out


@lru_cache(maxsize=16)
def _market_proxy_series(as_of_date: str | None = None) -> list[dict]:
    date_map: dict[str, list[float]] = {}
    for symbol in load_symbols():
        series = read_price_series(symbol, as_of_date=as_of_date)
        closes = [row.get('close', 0.0) for row in series]
        rebased = _rebase_base100(closes)
        for row, rebased_close in zip(series, rebased, strict=False):
            if rebased_close is None:
                continue
            date_map.setdefault(str(row.get('date', '')), []).append(rebased_close)

    return [
        {'date': date, 'value': round(mean(values), 4)}
        for date, values in sorted(date_map.items())
        if values
    ]


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------

def _benchmark_payload_for_symbol(symbol: str, as_of_date: str | None = None) -> dict:
    market = infer_market(symbol)
    benchmark = read_market_index_series(market, as_of_date=as_of_date)
    if benchmark:
        return {
            'label': market,
            'note': f'{market} 대표지수 기준 상대강도',
            'series': benchmark,
        }
    return {
        'label': '시장 프록시',
        'note': '실제 KOSPI/KOSDAQ 지수 데이터가 없어 현재 유니버스 평균을 시장 프록시로 사용',
        'series': _market_proxy_series(as_of_date=as_of_date),
    }


def _benchmark_payload_for_sector(members: list[str], as_of_date: str | None = None) -> dict:
    market_counts = Counter(infer_market(symbol) for symbol in members)
    if market_counts:
        market, count = max(sorted(market_counts.items()), key=lambda item: item[1])
        benchmark = read_market_index_series(market, as_of_date=as_of_date)
        if benchmark:
            note = f'{market} 대표지수 기준 섹터 상대강도'
            if len(market_counts) > 1:
                total = sum(market_counts.values())
                note = f'섹터 구성 종목 수 기준 {market} 비중 {count}/{total} 우세 벤치마크'
            return {
                'label': market,
                'note': note,
                'series': benchmark,
            }
    return {
        'label': '시장 프록시',
        'note': '실제 KOSPI/KOSDAQ 지수 데이터가 없어 현재 유니버스 평균을 시장 프록시로 사용',
        'series': _market_proxy_series(as_of_date=as_of_date),
    }


# ---------------------------------------------------------------------------
# Relative strength
# ---------------------------------------------------------------------------

def relative_strength_payload(symbol: str, price_series: list[dict], as_of_date: str | None = None) -> dict:
    dates = [str(row.get('date', '')) for row in price_series]
    closes = [float(row.get('close', 0.0) or 0.0) for row in price_series]
    benchmark_payload = _benchmark_payload_for_symbol(symbol, as_of_date=as_of_date)
    benchmark_series = benchmark_payload['series']
    market_map = {
        str(row.get('date', '')): float(row.get('close', row.get('value', 0.0)) or 0.0)
        for row in benchmark_series
    }
    benchmark_raw = [market_map.get(date) for date in dates]
    stock_base100 = _rebase_base100(closes)
    benchmark_base100 = _rebase_base100(benchmark_raw)

    rs_line: list[float | None] = []
    for stock_value, benchmark_value in zip(stock_base100, benchmark_base100, strict=False):
        if isinstance(stock_value, (int, float)) and isinstance(benchmark_value, (int, float)) and benchmark_value > 0:
            rs_line.append((float(stock_value) / float(benchmark_value)) * 100.0)
        else:
            rs_line.append(None)

    rs_ma20 = moving_average_nullable(rs_line, 20)
    valid_rs = [value for value in rs_line if isinstance(value, (int, float))]
    recent = valid_rs[-120:] if len(valid_rs) >= 120 else valid_rs
    rs_high_120 = max(recent) if recent else None
    latest = valid_rs[-1] if valid_rs else None
    latest_ma20 = next((value for value in reversed(rs_ma20) if isinstance(value, (int, float))), None)
    distance_to_high = ((latest / rs_high_120) - 1.0) * 100.0 if latest and rs_high_120 else None

    if latest and latest_ma20 and rs_high_120:
        if latest >= rs_high_120 * 0.995 and latest >= latest_ma20:
            state = 'rs_new_high'
        elif latest >= latest_ma20:
            state = 'rs_above_ma20'
        else:
            state = 'rs_below_ma20'
    else:
        state = 'unknown'

    percentile_map = _ret120_percentile_map(as_of_date=as_of_date)
    return {
        'benchmark_label': benchmark_payload['label'],
        'benchmark_note': benchmark_payload['note'],
        'rs_percentile_120': _round_or_none(percentile_map.get(symbol), digits=2),
        'latest': _round_or_none(latest, digits=2),
        'ma20': _round_or_none(latest_ma20, digits=2),
        'high120': _round_or_none(rs_high_120, digits=2),
        'distance_to_high120_pct': _round_or_none(distance_to_high, digits=2),
        'state': state,
        'line': _round_series(rs_line, digits=3),
        'ma20_line': _round_series(rs_ma20, digits=3),
        'benchmark_base100': _round_series(benchmark_base100, digits=3),
    }


# ---------------------------------------------------------------------------
# Volume signal
# ---------------------------------------------------------------------------

def volume_signal_payload(price_series: list[dict], volume_ma20: list[float | None]) -> dict:
    volumes = [float(row.get('volume', 0.0) or 0.0) for row in price_series]
    ratio_line: list[float | None] = []
    for volume, ma20_value in zip(volumes, volume_ma20, strict=False):
        if isinstance(ma20_value, (int, float)) and ma20_value and ma20_value > 0:
            ratio_line.append(volume / float(ma20_value))
        else:
            ratio_line.append(None)

    recent = [value for value in ratio_line[-20:] if isinstance(value, (int, float))]
    latest = next((value for value in reversed(ratio_line) if isinstance(value, (int, float))), None)
    expansion_days = sum(1 for value in recent if value >= 1.5)
    dryup_days = sum(1 for value in recent if value <= 0.8)

    if latest is None:
        state = 'unknown'
    elif latest >= 1.5:
        state = 'volume_expansion'
    elif latest <= 0.8:
        state = 'volume_dryup'
    else:
        state = 'normal'

    return {
        'latest_ratio_20': _round_or_none(latest, digits=3),
        'avg_ratio_20': _round_or_none(mean(recent), digits=3) if recent else None,
        'expansion_days_20': expansion_days,
        'dryup_days_20': dryup_days,
        'state': state,
        'ratio_20_line': _round_series(ratio_line, digits=3),
    }


# ---------------------------------------------------------------------------
# Sector breakout
# ---------------------------------------------------------------------------

@lru_cache(maxsize=256)
def sector_breakout_payload(sector: str, as_of_date: str | None = None) -> dict:
    members = [symbol for symbol in load_symbols() if get_sector(symbol, SECTOR_MAP) == sector]
    date_map: dict[str, list[float]] = {}
    volume_ratios: list[float] = []

    for symbol in members:
        series = read_price_series(symbol, as_of_date=as_of_date)
        closes = [row.get('close', 0.0) for row in series]
        rebased = _rebase_base100(closes)
        volumes = [row.get('volume', 0.0) for row in series]
        ma20 = moving_average(volumes, 20)
        for row, rebased_close in zip(series, rebased, strict=False):
            if rebased_close is None:
                continue
            date_map.setdefault(str(row.get('date', '')), []).append(rebased_close)

        if volumes and ma20 and isinstance(ma20[-1], (int, float)) and ma20[-1]:
            volume_ratios.append(float(volumes[-1]) / float(ma20[-1]))

    sector_proxy = [{'date': date, 'value': round(mean(values), 4)} for date, values in sorted(date_map.items()) if values]
    proxy_map = {str(row.get('date', '')): float(row.get('value', 0.0) or 0.0) for row in sector_proxy}
    benchmark_payload = _benchmark_payload_for_sector(members, as_of_date=as_of_date)
    market_map = {
        str(row.get('date', '')): float(row.get('close', row.get('value', 0.0)) or 0.0)
        for row in benchmark_payload['series']
    }
    common_dates = [date for date in proxy_map if date in market_map]
    common_dates.sort()

    sector_values = [proxy_map[date] for date in common_dates]
    market_values = [market_map[date] for date in common_dates]
    sector_base = _rebase_base100(sector_values)
    market_base = _rebase_base100(market_values)
    rs_line: list[float | None] = []
    for sector_value, market_value in zip(sector_base, market_base, strict=False):
        if isinstance(sector_value, (int, float)) and isinstance(market_value, (int, float)) and market_value > 0:
            rs_line.append((float(sector_value) / float(market_value)) * 100.0)
        else:
            rs_line.append(None)

    recent = [value for value in rs_line[-120:] if isinstance(value, (int, float))]
    latest = recent[-1] if recent else None
    high120 = max(recent) if recent else None
    distance = ((latest / high120) - 1.0) * 100.0 if latest and high120 else None
    participation = mean(min(1.0, max(0.0, value / 1.2)) for value in volume_ratios) if volume_ratios else 0.0
    breadth_ready = len(members) >= 2

    if latest and high120 and breadth_ready and latest >= high120 * 0.995 and participation >= 0.72:
        state = 'sector_breakout_confirmed'
    elif latest and high120 and breadth_ready and latest >= high120 * 0.97 and participation >= 0.45:
        state = 'sector_breakout_setup'
    else:
        state = 'sector_not_ready'

    return {
        'members': len(members),
        'benchmark_label': benchmark_payload['label'],
        'benchmark_note': benchmark_payload['note'],
        'latest_rs': _round_or_none(latest, digits=2),
        'high120': _round_or_none(high120, digits=2),
        'distance_to_high120_pct': _round_or_none(distance, digits=2),
        'volume_participation_ratio': _round_or_none(participation, digits=3),
        'breakout_state': state,
        'rs_line': _round_series(rs_line[-300:], digits=3),
        'dates': common_dates[-300:],
    }


# ---------------------------------------------------------------------------
# EPS quality
# ---------------------------------------------------------------------------

def eps_quality(eps_series: list[dict]) -> dict:
    if not eps_series:
        return {'status': 'missing', 'acceleration': 0.0, 'latest_yoy': 0.0}

    latest = eps_series[-1]
    yoy_values = [row.get('eps_yoy', 0.0) for row in eps_series if isinstance(row.get('eps_yoy'), (int, float))]
    acceleration = 0.0
    if len(yoy_values) >= 2:
        acceleration = yoy_values[-1] - yoy_values[-2]

    if latest.get('eps_yoy', 0.0) >= 20 and acceleration >= 0:
        status = 'strong_growth'
    elif latest.get('eps_yoy', 0.0) > 0:
        status = 'positive_growth'
    else:
        status = 'weak_or_negative'

    return {
        'status': status,
        'acceleration': round(acceleration, 2),
        'latest_yoy': round(float(latest.get('eps_yoy', 0.0)), 2),
    }


# ---------------------------------------------------------------------------
# Trend template
# ---------------------------------------------------------------------------

def trend_template_snapshot(price_series: list[dict], ma_map: dict[str, list[float | None]], macd_payload: dict) -> dict:
    closes = [row.get('close', 0.0) for row in price_series]
    volumes = [row.get('volume', 0.0) for row in price_series]
    if not closes:
        return {
            'checks': {},
            'passed_count': 0,
            'distance_to_high52_pct': None,
            'distance_from_low52_pct': None,
            'volume_dryup_ratio': None,
            'current_volume_ratio_to_avg20': None,
            'tightness_ratio_20_60': None,
            'macd_state': 'unknown',
        }

    close = closes[-1]
    sma50 = ma_map['sma50'][-1]
    sma150 = ma_map['sma150'][-1]
    sma200 = ma_map['sma200'][-1]
    high52 = max(closes[-252:] if len(closes) >= 252 else closes)
    low52 = min(closes[-252:] if len(closes) >= 252 else closes)

    avg20 = mean(volumes[-20:]) if len(volumes) >= 20 else (mean(volumes) if volumes else 0.0)
    avg60 = mean(volumes[-60:]) if len(volumes) >= 60 else avg20
    recent20 = mean(volumes[-20:]) if len(volumes) >= 20 else avg20
    volume_dryup_ratio = (recent20 / avg60) if avg60 else None
    current_volume_ratio = (volumes[-1] / avg20) if avg20 else None

    returns = []
    for idx in range(1, len(closes)):
        prev = closes[idx - 1]
        cur = closes[idx]
        returns.append((cur / prev - 1.0) if prev > 0 else 0.0)
    recent_rets = returns[-20:] if len(returns) >= 20 else returns
    base_rets = returns[-60:-20] if len(returns) >= 60 else returns[:-20]
    if recent_rets and base_rets and pstdev(base_rets) > 0:
        tightness_ratio = pstdev(recent_rets) / pstdev(base_rets)
    else:
        tightness_ratio = None

    macd_line = macd_payload.get('line', [])
    signal_line = macd_payload.get('signal', [])
    hist_line = macd_payload.get('histogram', [])
    if macd_line and signal_line and hist_line:
        if macd_line[-1] >= signal_line[-1] and hist_line[-1] >= 0:
            macd_state = 'bullish'
        elif macd_line[-1] < signal_line[-1] and hist_line[-1] < 0:
            macd_state = 'bearish'
        else:
            macd_state = 'mixed'
    else:
        macd_state = 'unknown'

    checks = {
        'sma50_gt_sma150_gt_sma200': bool(sma50 and sma150 and sma200 and sma50 > sma150 > sma200),
        'close_gt_sma50': bool(sma50 and close > sma50),
        'close_within_25pct_of_52w_high': bool(high52 and close >= high52 * 0.75),
        'close_25pct_above_52w_low': bool(low52 and close >= low52 * 1.25),
        'volume_dryup_ok': bool(volume_dryup_ratio is not None and volume_dryup_ratio <= 0.85),
        'macd_20_60_bullish': macd_state == 'bullish',
    }

    return {
        'close': round(close, 2),
        'sma20': _round_or_none(ma_map['sma20'][-1]),
        'sma50': _round_or_none(sma50),
        'sma60': _round_or_none(ma_map['sma60'][-1]),
        'sma150': _round_or_none(sma150),
        'sma200': _round_or_none(sma200),
        'high52': round(high52, 2),
        'low52': round(low52, 2),
        'distance_to_high52_pct': round(((close / high52) - 1.0) * 100.0, 2) if high52 else None,
        'distance_from_low52_pct': round(((close / low52) - 1.0) * 100.0, 2) if low52 else None,
        'volume_dryup_ratio': _round_or_none(volume_dryup_ratio, digits=3),
        'current_volume_ratio_to_avg20': _round_or_none(current_volume_ratio, digits=3),
        'tightness_ratio_20_60': _round_or_none(tightness_ratio, digits=3),
        'macd_state': macd_state,
        'checks': checks,
        'passed_count': sum(1 for value in checks.values() if value),
    }


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

@lru_cache(maxsize=128)
def build_stock_analysis(symbol: str, as_of_date: str | None = None) -> dict:
    price_series = read_price_series(symbol, as_of_date=as_of_date)
    if not price_series:
        return {'symbol': symbol, 'name': get_symbol_name(symbol), 'error': 'no_price_data'}
    eps_series = read_eps_series(symbol, as_of_date=as_of_date)

    closes = [row.get('close', 0.0) for row in price_series]
    volumes = [row.get('volume', 0.0) for row in price_series]

    ma_map = {
        'sma20': moving_average(closes, 20),
        'sma50': moving_average(closes, 50),
        'sma60': moving_average(closes, 60),
        'sma150': moving_average(closes, 150),
        'sma200': moving_average(closes, 200),
        'volume_ma20': moving_average(volumes, 20),
    }
    macd_payload = macd(closes, fast=20, slow=60, signal_window=9)
    lr = least_resistance(price_series)
    lr_line = least_resistance_line(price_series)
    epsq = eps_quality(eps_series)
    template = trend_template_snapshot(price_series, ma_map, macd_payload)
    rs_payload = relative_strength_payload(symbol, price_series, as_of_date=as_of_date)
    volume_signal = volume_signal_payload(price_series, ma_map['volume_ma20'])
    cwh = detect_cup_with_handle(price_series)
    sector = get_sector(symbol, SECTOR_MAP)
    sector_strength = sector_breakout_payload(sector, as_of_date=as_of_date)
    company_facts = estimated_market_cap(symbol, template.get('close'))

    tail = 300
    return {
        'symbol': symbol,
        'name': get_symbol_name(symbol),
        'sector': sector,
        'as_of_date': price_series[-1]['date'] if price_series else as_of_date,
        'close_series': price_series[-tail:],
        'eps_series': eps_series,
        'company_facts': {
            'shares_outstanding': company_facts.get('shares_outstanding'),
            'last_price_latest': _round_or_none(company_facts.get('last_price_latest'), digits=2),
            'market_cap_latest': _round_or_none(company_facts.get('market_cap_latest'), digits=0),
            'market_cap_estimated': _round_or_none(company_facts.get('market_cap_estimated'), digits=0),
            'market_cap_basis': company_facts.get('market_cap_basis'),
            'currency': company_facts.get('currency') or 'KRW',
        },
        'least_resistance': lr,
        'eps_quality': epsq,
        'trend_template': template,
        'relative_strength': {
            **rs_payload,
            'line': rs_payload.get('line', [])[-tail:],
            'ma20_line': rs_payload.get('ma20_line', [])[-tail:],
            'benchmark_base100': rs_payload.get('benchmark_base100', [])[-tail:],
        },
        'volume_signal': {
            **volume_signal,
            'ratio_20_line': volume_signal.get('ratio_20_line', [])[-tail:],
        },
        'cup_with_handle': cwh,
        'sector_strength': sector_strength,
        'indicators': {
            'sma20': _round_series(ma_map['sma20'][-tail:]),
            'sma50': _round_series(ma_map['sma50'][-tail:]),
            'sma60': _round_series(ma_map['sma60'][-tail:]),
            'sma150': _round_series(ma_map['sma150'][-tail:]),
            'sma200': _round_series(ma_map['sma200'][-tail:]),
            'volume_ma20': _round_series(ma_map['volume_ma20'][-tail:], digits=0),
            'volume_ratio_20': volume_signal.get('ratio_20_line', [])[-tail:],
            'least_resistance_line': _round_series(lr_line[-tail:]),
            'macd_20_60': {
                'fast': macd_payload['fast'],
                'slow': macd_payload['slow'],
                'signal_window': macd_payload['signal_window'],
                'line': macd_payload['line'][-tail:],
                'signal': macd_payload['signal'][-tail:],
                'histogram': macd_payload['histogram'][-tail:],
            },
        },
    }
