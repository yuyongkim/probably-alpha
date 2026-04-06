"""On-the-fly stock screener for backtests.

Supports 4 signal types:
  trend_template  — Minervini TT 8-check + RS percentile
  channel_breakout — Donchian N-day high breakout (Dennis/Turtle)
  value_screen    — PER/PBR/ROE screening (Greenblatt)
  swing           — Short-term volatility contraction + breakout
"""
from __future__ import annotations

from statistics import mean

from sepa.backtest.strategy import StrategyConfig
from sepa.data.sector_map import get_sector, load_sector_map
from sepa.data.universe import get_symbol_name

_SECTOR_MAP = None


def _get_sector_map():
    global _SECTOR_MAP
    if _SECTOR_MAP is None:
        _SECTOR_MAP = load_sector_map()
    return _SECTOR_MAP


def screen_universe(
    config: StrategyConfig,
    price_data: dict[str, dict],
    fundamentals: dict[str, dict] | None = None,
    market_close: float | None = None,
    market_ma200: float | None = None,
) -> list[dict]:
    """Screen all symbols using strategy-specific signal generation.

    Parameters
    ----------
    config : StrategyConfig
    price_data : {symbol: {closes, volumes}} — pre-loaded, possibly sliced
    fundamentals : {symbol: {eps_yoy, revenue_yoy, roe, per, pbr, ...}}
    market_close : KOSPI close price (for market filter)
    market_ma200 : KOSPI 200-day MA (for market filter)
    """
    # Market regime filter (Jones, Dalio)
    if config.use_market_filter and market_close and market_ma200:
        if market_close < market_ma200:
            # Bear market — reduce or skip entirely
            if config.cash_in_bear_pct >= 1.0:
                return []  # 100% cash, no signals

    dispatch = {
        'trend_template': _screen_trend_template,
        'channel_breakout': _screen_channel_breakout,
        'value_screen': _screen_value,
        'swing': _screen_swing,
    }
    screener = dispatch.get(config.signal_type, _screen_trend_template)
    candidates = screener(config, price_data, fundamentals)

    if not candidates:
        return []

    # Sector filtering (shared across all types)
    sector_map = _get_sector_map()
    for c in candidates:
        if 'sector' not in c:
            c['sector'] = get_sector(c['symbol'], sector_map)

    if config.sector_filter:
        sector_scores: dict[str, float] = {}
        for c in candidates:
            sec = c.get('sector', 'Other')
            sector_scores[sec] = sector_scores.get(sec, 0) + c.get('score', 0)
        top_secs = sorted(sector_scores, key=sector_scores.get, reverse=True)[:config.top_sectors]
        candidates = [c for c in candidates if c.get('sector', 'Other') in top_secs]

    # Sector limit
    if config.sector_limit > 0:
        sector_count: dict[str, int] = {}
        limited: list[dict] = []
        for c in sorted(candidates, key=lambda x: x.get('score', 0), reverse=True):
            sec = c.get('sector', 'Other')
            if sector_count.get(sec, 0) < config.sector_limit:
                limited.append(c)
                sector_count[sec] = sector_count.get(sec, 0) + 1
        candidates = limited

    candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
    result = candidates[:config.max_positions * 2]

    # Enrich with execution plan (stop/target/sizing)
    for c in result:
        _enrich_execution_plan(c, config)

    return result


def _enrich_execution_plan(candidate: dict, config) -> None:
    """Add stop_price, target_price, rr_ratio, position sizing to each candidate."""
    close = candidate.get('close', 0)
    atr = candidate.get('atr', 0)
    if close <= 0:
        return

    # Stop price
    if config.stop_type == 'atr_trailing' and atr > 0:
        stop = close - atr * config.atr_stop_multiplier
    elif config.stop_type == 'ma_trailing':
        stop = candidate.get('sma50', close * 0.9) if config.ma_exit_period <= 50 else candidate.get('sma200', close * 0.85)
    elif config.stop_type == 'channel_exit' and 'channel_low' in candidate:
        stop = candidate['channel_low']
    else:
        stop = close * (1.0 - config.stop_loss_pct)

    risk_per_share = max(close - stop, close * 0.01)

    # Target price
    if config.profit_target_pct > 0:
        target = close * (1.0 + config.profit_target_pct)
    else:
        target = close + risk_per_share * 2.0  # default 2R

    rr = (target - close) / risk_per_share if risk_per_share > 0 else 0

    # Position sizing
    equity = config.initial_cash
    per_position = equity / max(1, config.max_positions)

    if config.sizing_method == 'atr_risk' and atr > 0:
        stop_dist = atr * config.atr_stop_multiplier
        shares = int((equity * config.risk_per_trade_pct) / stop_dist) if stop_dist > 0 else 0
        position_value = shares * close
    else:
        position_value = per_position
        shares = int(per_position / close) if close > 0 else 0

    max_loss = shares * risk_per_share
    # max_loss_pct is relative to the POSITION value, not total equity
    max_loss_pct_of_position = round(risk_per_share / close * 100, 1) if close > 0 else 0
    max_loss_pct_of_equity = round(max_loss / equity * 100, 2) if equity > 0 else 0

    candidate['execution'] = {
        'entry_price': int(round(close)),
        'stop_price': int(round(stop)),
        'target_price': int(round(target)),
        'rr_ratio': round(rr, 2),
        'shares': shares,
        'position_value': int(round(position_value)),
        'max_loss_krw': int(round(max_loss)),
        'max_loss_pct': max_loss_pct_of_position,  # % of position
        'max_loss_pct_equity': max_loss_pct_of_equity,  # % of total equity
        'stop_type': config.stop_type,
        'sizing_method': config.sizing_method,
    }


# ── Trend Template (Minervini/O'Neil/Seykota) ────────────────────────────

def _screen_trend_template(
    config: StrategyConfig,
    price_data: dict[str, dict],
    fundamentals: dict[str, dict] | None = None,
) -> list[dict]:
    candidates: list[dict] = []
    rs_values: dict[str, float] = {}

    for symbol, data in price_data.items():
        closes = data.get('closes', [])
        volumes = data.get('volumes', [])
        if len(closes) < 200:
            continue

        close = closes[-1]
        sma50 = mean(closes[-50:])
        sma150 = mean(closes[-150:])
        sma200 = mean(closes[-200:])
        sma200_prev20 = mean(closes[-220:-20]) if len(closes) >= 220 else sma200

        w = closes[-252:] if len(closes) >= 252 else closes
        high52 = max(w)
        low52 = min(w)

        base = closes[-121] if len(closes) >= 121 else closes[0]
        ret120 = (close / base - 1.0) if base > 0 else 0.0
        rs_values[symbol] = ret120

        # TT 8 checks
        checks = {
            'c1_ma_alignment': sma50 > sma150 > sma200,
            'c2_close_gt_sma50': close > sma50,
            'c3_sma150_gt_sma200': sma150 > sma200,
            'c4_sma200_rising': sma200 > sma200_prev20,
            'c5_above_52w_low': close >= (config.c5_multiplier * low52) if low52 > 0 else True,
            'c6_near_52w_high': close >= (config.c6_multiplier * high52) if high52 > 0 else True,
            'c7_rs_placeholder': True,
            'c8_close_gt_sma200': close > sma200,
        }

        if config.require_ma50 and not checks['c2_close_gt_sma50']:
            continue
        if config.require_close_gt_sma200 and not checks['c8_close_gt_sma200']:
            continue

        passed = sum(1 for v in checks.values() if v)
        if passed < config.min_tt_pass:
            continue

        # Volume expansion
        if config.require_volume_expansion and len(volumes) >= 50:
            vol_short = mean(volumes[-5:]) if volumes[-5:] else 0
            vol_long = mean(volumes[-50:]) if volumes[-50:] else 1
            if vol_long > 0 and vol_short / vol_long < config.min_volume_ratio:
                continue

        # Near 52w high
        if config.require_near_52w_high:
            if high52 > 0 and close < config.near_52w_threshold * high52:
                continue

        # Volatility contraction
        if config.require_volatility_contraction and len(closes) >= 50:
            atr10 = mean([abs(closes[i] - closes[i - 1]) for i in range(-9, 0)])
            atr50 = mean([abs(closes[i] - closes[i - 1]) for i in range(-49, 0)])
            if atr50 > 0 and atr10 / atr50 >= 1.0:
                continue

        # 20d breakout
        if config.require_20d_breakout and len(closes) >= 20:
            if close < max(closes[-20:]):
                continue

        # Earnings filter
        if config.use_earnings_filter and fundamentals:
            fund = fundamentals.get(symbol, {})
            eps_yoy = fund.get('eps_yoy', 0)
            rev_yoy = fund.get('revenue_yoy', 0)
            if eps_yoy < config.min_eps_growth_yoy:
                continue
            if config.min_revenue_growth_yoy > 0 and rev_yoy < config.min_revenue_growth_yoy:
                continue
            if config.require_eps_acceleration:
                eps_accel = fund.get('eps_acceleration', 0)
                if eps_accel <= 0:
                    continue
            if config.min_roe > 0:
                roe = fund.get('roe', 0)
                if roe < config.min_roe:
                    continue

        # ATR for sizing
        atr = _compute_atr(closes, config.atr_period)

        candidates.append({
            'symbol': symbol,
            'name': get_symbol_name(symbol),
            'close': close,
            'sma50': sma50,
            'sma200': sma200,
            'high52': high52,
            'ret120': ret120,
            'tt_passed': passed,
            'atr': atr,
            'checks': checks,
        })

    if not candidates:
        return []

    # RS percentile
    rs_sorted = sorted(rs_values.values())
    n = len(rs_sorted)
    for c in candidates:
        ret = c['ret120']
        rank = sum(1 for v in rs_sorted if v <= ret)
        rs_pct = (rank / n * 100) if n > 0 else 50
        c['rs_percentile'] = round(rs_pct, 2)
        c['checks']['c7_rs_placeholder'] = rs_pct >= config.rs_threshold
        if rs_pct < config.rs_threshold:
            c['tt_passed'] -= 1

    candidates = [c for c in candidates if c['rs_percentile'] >= config.rs_threshold]
    candidates = [c for c in candidates if c['tt_passed'] >= config.min_tt_pass]

    for c in candidates:
        tt_score = c['tt_passed'] / 8.0 * 50
        rs_score = c['rs_percentile'] / 100.0 * 50
        c['score'] = round(tt_score + rs_score, 1)

    return candidates


# ── Channel Breakout (Dennis/Turtle) ─────────────────────────────────────

def _screen_channel_breakout(
    config: StrategyConfig,
    price_data: dict[str, dict],
    fundamentals: dict[str, dict] | None = None,
) -> list[dict]:
    candidates: list[dict] = []
    n = config.channel_entry_period

    for symbol, data in price_data.items():
        closes = data.get('closes', [])
        volumes = data.get('volumes', [])
        if len(closes) < max(n + 1, 50):
            continue

        close = closes[-1]
        prev_close = closes[-2]
        channel_high = max(closes[-n - 1:-1])  # N-day high BEFORE today

        # Breakout: today's close > N-day high
        if close <= channel_high:
            continue

        # Volume confirmation
        if config.require_channel_volume and len(volumes) >= 20:
            vol_today = volumes[-1]
            vol_avg = mean(volumes[-20:])
            if vol_avg > 0 and vol_today < vol_avg * 1.2:
                continue

        atr = _compute_atr(closes, config.atr_period)
        ret120 = (close / closes[-121] - 1.0) if len(closes) >= 121 and closes[-121] > 0 else 0.0

        # Score: breakout strength (how far above channel)
        breakout_pct = (close / channel_high - 1.0) * 100 if channel_high > 0 else 0
        score = min(breakout_pct * 10, 100)  # normalize

        candidates.append({
            'symbol': symbol,
            'name': get_symbol_name(symbol),
            'close': close,
            'channel_high': channel_high,
            'breakout_pct': round(breakout_pct, 2),
            'atr': atr,
            'ret120': ret120,
            'score': round(score, 1),
        })

    return candidates


# ── Value Screen (Greenblatt Magic Formula) ──────────────────────────────

def _screen_value(
    config: StrategyConfig,
    price_data: dict[str, dict],
    fundamentals: dict[str, dict] | None = None,
) -> list[dict]:
    if not fundamentals:
        return []

    candidates: list[dict] = []
    for symbol, fund in fundamentals.items():
        per = fund.get('per')
        pbr = fund.get('pbr')
        roe = fund.get('roe')
        debt = fund.get('debt_ratio')

        # Skip if no data
        if per is None or pbr is None or roe is None:
            continue

        # Filters
        if per <= 0 or per > config.max_per:
            continue
        if pbr > config.max_pbr:
            continue
        if roe < config.min_roe_value:
            continue
        if debt is not None and config.max_debt_ratio > 0 and debt > config.max_debt_ratio:
            continue

        # Need price data for the symbol
        if symbol not in price_data:
            continue
        closes = price_data[symbol].get('closes', [])
        if len(closes) < 50:
            continue

        close = closes[-1]
        atr = _compute_atr(closes, config.atr_period)

        # Magic formula score: rank by earnings yield (1/PER) + ROE
        earnings_yield = 1.0 / per if per > 0 else 0
        score = round((earnings_yield * 50 + roe / 100 * 50) * 100, 1)

        candidates.append({
            'symbol': symbol,
            'name': get_symbol_name(symbol),
            'close': close,
            'per': per,
            'pbr': pbr,
            'roe': roe,
            'atr': atr,
            'score': score,
        })

    return candidates


# ── Swing (Schwartz/Raschke) ─────────────────────────────────────────────

def _screen_swing(
    config: StrategyConfig,
    price_data: dict[str, dict],
    fundamentals: dict[str, dict] | None = None,
) -> list[dict]:
    candidates: list[dict] = []

    for symbol, data in price_data.items():
        closes = data.get('closes', [])
        volumes = data.get('volumes', [])
        if len(closes) < 50:
            continue

        close = closes[-1]
        sma10 = mean(closes[-10:])
        sma20 = mean(closes[-20:])
        sma50 = mean(closes[-50:])

        # Must be above short-term MA
        if config.require_ma50 and close <= sma50:
            continue
        if close <= sma10:
            continue

        # Volatility contraction: NR7 (narrowest range in 7 days)
        if config.require_volatility_contraction:
            ranges = [abs(closes[i] - closes[i - 1]) for i in range(-6, 0)]
            today_range = abs(close - closes[-2])
            if today_range > min(ranges):
                continue

        # 20d breakout
        if config.require_20d_breakout and len(closes) >= 20:
            if close < max(closes[-20:]):
                continue

        atr = _compute_atr(closes, config.atr_period)
        ret120 = (close / closes[-121] - 1.0) if len(closes) >= 121 and closes[-121] > 0 else 0.0

        # Score: proximity to breakout + volume
        dist_to_high20 = (close / max(closes[-20:]) - 1.0) * 100 if len(closes) >= 20 else 0
        score = max(0, 50 + dist_to_high20 * 10)

        candidates.append({
            'symbol': symbol,
            'name': get_symbol_name(symbol),
            'close': close,
            'sma10': sma10,
            'sma20': sma20,
            'atr': atr,
            'ret120': ret120,
            'score': round(score, 1),
        })

    return candidates


# ── Helpers ──────────────────────────────────────────────────────────────

def _compute_atr(closes: list[float], period: int = 14) -> float:
    """Average True Range from close-only data (approximation)."""
    if len(closes) < period + 1:
        return 0.0
    trs = [abs(closes[i] - closes[i - 1]) for i in range(-period, 0)]
    return mean(trs) if trs else 0.0
