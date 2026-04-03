"""On-the-fly stock screener for backtests.

Runs Alpha TT checks + extra conditions using StrategyConfig parameters.
Uses pre-loaded price data (not file-based signals).
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
    date_index: dict[str, int] | None = None,
    as_of_date: str | None = None,
) -> list[dict]:
    """Screen all symbols using Alpha TT + extra conditions.

    Parameters
    ----------
    config : StrategyConfig
    price_data : dict
        {symbol: {closes: list[float], volumes: list[float], dates: list[str]}}
        Pre-loaded from ohlcv_db, possibly sliced to as_of_date.
    date_index : dict, optional
        {date_str: index} for slicing if price_data contains full history.
    as_of_date : str, optional
        Used for slicing if date_index provided.

    Returns
    -------
    list[dict] sorted by score descending.
    """
    sector_map = _get_sector_map()

    # Compute metrics for all symbols
    candidates: list[dict] = []
    rs_values: dict[str, float] = {}

    for symbol, data in price_data.items():
        closes = data.get('closes', [])
        volumes = data.get('volumes', [])

        # Slice to as_of_date if needed
        if as_of_date and date_index and 'dates' in data:
            dates = data['dates']
            cutoff_idx = None
            for i, d in enumerate(dates):
                if d.replace('-', '') <= as_of_date.replace('-', ''):
                    cutoff_idx = i
            if cutoff_idx is not None:
                closes = closes[:cutoff_idx + 1]
                volumes = volumes[:cutoff_idx + 1]

        if len(closes) < 200:
            continue

        # Compute TT metrics
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
            'c7_rs_placeholder': True,  # filled after percentile
            'c8_close_gt_sma200': close > sma200,
        }

        # Hard gates
        if config.require_ma50 and not checks['c2_close_gt_sma50']:
            continue
        if config.require_close_gt_sma200 and not checks['c8_close_gt_sma200']:
            continue

        passed = sum(1 for v in checks.values() if v)
        if passed < config.min_tt_pass:
            continue

        # Extra conditions
        if config.require_volume_expansion and len(volumes) >= 50:
            vol_short = mean(volumes[-5:]) if volumes[-5:] else 0
            vol_long = mean(volumes[-50:]) if volumes[-50:] else 1
            if vol_long > 0 and vol_short / vol_long < config.min_volume_ratio:
                continue

        if config.require_near_52w_high:
            if high52 > 0 and close < config.near_52w_threshold * high52:
                continue

        if config.require_volatility_contraction and len(closes) >= 50:
            atr10 = mean([abs(closes[i] - closes[i - 1]) for i in range(-9, 0)])
            atr50 = mean([abs(closes[i] - closes[i - 1]) for i in range(-49, 0)])
            if atr50 > 0 and atr10 / atr50 >= 1.0:  # not contracting
                continue

        if config.require_20d_breakout and len(closes) >= 20:
            high20 = max(closes[-20:])
            if close < high20:
                continue

        candidates.append({
            'symbol': symbol,
            'name': get_symbol_name(symbol),
            'sector': get_sector(symbol, sector_map),
            'close': close,
            'sma50': sma50,
            'sma200': sma200,
            'high52': high52,
            'ret120': ret120,
            'tt_passed': passed,
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

        # Recheck TT with RS
        if rs_pct < config.rs_threshold:
            c['tt_passed'] -= 1  # c7 fails

    # Filter by RS threshold (recheck after percentile)
    candidates = [c for c in candidates if c['rs_percentile'] >= config.rs_threshold]

    # Filter by min TT pass (recheck)
    candidates = [c for c in candidates if c['tt_passed'] >= config.min_tt_pass]

    # Score (0~100 normalized)
    for c in candidates:
        tt_score = c['tt_passed'] / 8.0 * 50  # max 50
        rs_score = c['rs_percentile'] / 100.0 * 50  # max 50
        c['score'] = round(tt_score + rs_score, 1)  # max 100

    # Sector filtering
    if config.sector_filter:
        sector_scores: dict[str, float] = {}
        for c in candidates:
            sec = c['sector']
            sector_scores[sec] = sector_scores.get(sec, 0) + c['score']
        top_secs = sorted(sector_scores, key=sector_scores.get, reverse=True)[:config.top_sectors]
        candidates = [c for c in candidates if c['sector'] in top_secs]

    # Sort by score
    candidates.sort(key=lambda x: x['score'], reverse=True)

    # Sector limit
    if config.sector_limit > 0:
        sector_count: dict[str, int] = {}
        limited: list[dict] = []
        for c in candidates:
            sec = c['sector']
            if sector_count.get(sec, 0) < config.sector_limit:
                limited.append(c)
                sector_count[sec] = sector_count.get(sec, 0) + 1
        candidates = limited

    return candidates[:config.max_positions * 2]  # Return 2x for flexibility
