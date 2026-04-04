"""Chart pattern detection (Cup-with-Handle, etc.)."""
from __future__ import annotations

import math


def _smooth(prices: list[float], window: int = 5) -> list[float]:
    """Simple moving average smoothing to reduce noise."""
    if window < 2 or len(prices) < window:
        return list(prices)
    out: list[float] = []
    s = sum(prices[:window])
    for i in range(len(prices)):
        if i >= window:
            s += prices[i] - prices[i - window]
        w = min(i + 1, window)
        out.append(s / w if i >= window - 1 else sum(prices[:i + 1]) / (i + 1))
    return out


def _find_local_highs(closes: list[float], order: int = 10) -> list[int]:
    """Find local maxima indices with given look-left/look-right order."""
    highs = []
    for i in range(order, len(closes) - order):
        if all(closes[i] >= closes[i - j] for j in range(1, order + 1)) and \
           all(closes[i] >= closes[i + j] for j in range(1, order + 1)):
            highs.append(i)
    return highs


def _find_local_lows(closes: list[float], order: int = 10) -> list[int]:
    """Find local minima indices."""
    lows = []
    for i in range(order, len(closes) - order):
        if all(closes[i] <= closes[i - j] for j in range(1, order + 1)) and \
           all(closes[i] <= closes[i + j] for j in range(1, order + 1)):
            lows.append(i)
    return lows


def _cup_symmetry(closes: list[float], left_idx: int, bottom_idx: int, right_idx: int) -> float:
    """Score cup symmetry (0-1). Higher = more symmetric U-shape."""
    left_len = bottom_idx - left_idx
    right_len = right_idx - bottom_idx
    if left_len <= 0 or right_len <= 0:
        return 0.0
    ratio = min(left_len, right_len) / max(left_len, right_len)
    return ratio


def detect_cup_with_handle(
    price_series: list[dict],
    min_cup_days: int = 20,
    max_cup_days: int = 200,
) -> dict:
    """Detect a Cup-with-Handle (CWH) chart pattern.

    Multi-candidate approach: scans multiple potential left rims (local highs)
    and picks the best-scoring cup formation.

    Cup depth: 10-50% from the left rim (relaxed for KRX volatility).
    Handle depth: 2-15% from the right rim.
    """
    default = {
        'detected': False,
        'cup_depth_pct': 0.0,
        'handle_depth_pct': 0.0,
        'pivot_price': 0.0,
        'cup_days': 0,
        'handle_days': 0,
        'cup_start_date': '',
        'handle_start_date': '',
        'stage': 'none',
        'score': 0.0,
    }

    closes = [float(row.get('close', 0.0)) for row in price_series if row.get('close', 0.0) > 0]
    dates = [str(row.get('date', '')) for row in price_series if row.get('close', 0.0) > 0]

    if len(closes) < min_cup_days + 10:
        return default

    # Lookback window
    lookback = min(len(closes), max_cup_days + 50)
    wc = closes[-lookback:]
    wd = dates[-lookback:]
    n = len(wc)

    # Smooth prices for peak/trough detection (raw prices for depth calc)
    smoothed = _smooth(wc, window=5)

    # Find candidate left rims: local highs on smoothed data
    local_highs = _find_local_highs(smoothed, order=8)
    # Also consider the absolute high as a candidate
    abs_high_idx = max(range(n), key=lambda i: wc[i])
    if abs_high_idx not in local_highs:
        local_highs.append(abs_high_idx)
    # Sort and keep only those with enough room for a cup after them
    local_highs = sorted(h for h in local_highs if h < n - min_cup_days)

    if not local_highs:
        return default

    best: dict | None = None
    best_score = -1.0

    for left_rim_idx in local_highs:
        left_rim_price = wc[left_rim_idx]
        if left_rim_price <= 0:
            continue

        # Find cup bottom: lowest point after left rim within max_cup_days
        search_end = min(n, left_rim_idx + max_cup_days + 1)
        if left_rim_idx + 5 >= search_end:
            continue

        cup_bottom_idx = left_rim_idx + 1
        cup_bottom_price = wc[left_rim_idx + 1]
        for i in range(left_rim_idx + 2, search_end):
            if wc[i] < cup_bottom_price:
                cup_bottom_price = wc[i]
                cup_bottom_idx = i

        cup_depth_pct = ((left_rim_price - cup_bottom_price) / left_rim_price) * 100.0

        # Cup depth: 10-50% (relaxed for KRX)
        if cup_depth_pct < 10.0 or cup_depth_pct > 50.0:
            if 7.0 <= cup_depth_pct < 10.0:
                # Shallow cup still forming — track as candidate
                cand = {
                    **default,
                    'cup_depth_pct': round(cup_depth_pct, 2),
                    'cup_days': cup_bottom_idx - left_rim_idx,
                    'cup_start_date': wd[left_rim_idx] if left_rim_idx < len(wd) else '',
                    'stage': 'cup_forming',
                    'score': 0.1,
                }
                if cand['score'] > best_score:
                    best_score = cand['score']
                    best = cand
            continue

        # Find right rim: price recovery after bottom
        # Relaxed: require recovery to 80% of left rim (was 85%)
        right_rim_idx = None
        right_rim_price = 0.0
        for i in range(cup_bottom_idx + 1, n):
            if wc[i] >= left_rim_price * 0.80:
                right_rim_idx = i
                right_rim_price = wc[i]
                break

        cup_days = (right_rim_idx - left_rim_idx) if right_rim_idx is not None else (cup_bottom_idx - left_rim_idx)

        if right_rim_idx is None:
            # Cup bottom found but no recovery yet
            recent = wc[max(cup_bottom_idx, n - 10):]
            rising = len(recent) >= 3 and recent[-1] > recent[0]
            # Also check how close we are to recovery
            current = wc[-1]
            recovery_pct = ((current - cup_bottom_price) / (left_rim_price - cup_bottom_price)) * 100.0 if left_rim_price > cup_bottom_price else 0.0
            if rising or recovery_pct > 60:
                cand = {
                    **default,
                    'cup_depth_pct': round(cup_depth_pct, 2),
                    'cup_days': cup_bottom_idx - left_rim_idx,
                    'cup_start_date': wd[left_rim_idx] if left_rim_idx < len(wd) else '',
                    'stage': 'cup_forming',
                    'score': 0.2 + recovery_pct / 500.0,
                }
                if cand['score'] > best_score:
                    best_score = cand['score']
                    best = cand
            continue

        # Validate cup duration
        if cup_days < min_cup_days or cup_days > max_cup_days:
            continue

        # Cup symmetry score
        symmetry = _cup_symmetry(wc, left_rim_idx, cup_bottom_idx, right_rim_idx)

        # Step 4: Handle detection
        remaining = n - right_rim_idx - 1

        if remaining < 2:
            # Right rim just formed
            score = 0.3 + symmetry * 0.2
            cand = {
                **default,
                'cup_depth_pct': round(cup_depth_pct, 2),
                'cup_days': cup_days,
                'cup_start_date': wd[left_rim_idx] if left_rim_idx < len(wd) else '',
                'stage': 'cup_forming',
                'score': round(score, 3),
            }
            if score > best_score:
                best_score = score
                best = cand
            continue

        # Find handle high (start of pullback) and handle low
        handle_start_idx = right_rim_idx
        handle_high = right_rim_price
        handle_search_end = min(n, right_rim_idx + 30)
        for i in range(right_rim_idx, handle_search_end):
            if wc[i] > handle_high:
                handle_high = wc[i]
                handle_start_idx = i

        # Find handle low after handle start
        handle_low = handle_high
        handle_low_idx = handle_start_idx
        for i in range(handle_start_idx, n):
            if wc[i] < handle_low:
                handle_low = wc[i]
                handle_low_idx = i

        handle_depth_pct = ((handle_high - handle_low) / handle_high) * 100.0 if handle_high > 0 else 0.0
        handle_days = n - 1 - handle_start_idx

        # Pivot (buy point)
        pivot_price = round(handle_high * 1.005, 2)

        # Score the candidate
        # Prefer: moderate cup depth (15-33%), good symmetry, valid handle
        depth_score = 1.0 - abs(cup_depth_pct - 25.0) / 25.0
        depth_score = max(0.0, depth_score)

        if 2.0 <= handle_depth_pct <= 15.0 and 3 <= handle_days <= 40:
            # Valid handle
            current_price = wc[-1]
            if current_price >= handle_high * 0.995:
                stage = 'breakout_ready'
                stage_bonus = 0.3
            elif current_price >= handle_low + (handle_high - handle_low) * 0.5:
                stage = 'handle_forming'
                stage_bonus = 0.15
            else:
                stage = 'handle_forming'
                stage_bonus = 0.1

            # Handle depth sweet spot: 5-12%
            handle_score = 1.0 - abs(handle_depth_pct - 8.0) / 12.0
            handle_score = max(0.0, handle_score)

            score = 0.4 + depth_score * 0.15 + symmetry * 0.15 + handle_score * 0.15 + stage_bonus
            cand = {
                'detected': True,
                'cup_depth_pct': round(cup_depth_pct, 2),
                'handle_depth_pct': round(handle_depth_pct, 2),
                'pivot_price': pivot_price,
                'cup_days': cup_days,
                'handle_days': handle_days,
                'cup_start_date': wd[left_rim_idx] if left_rim_idx < len(wd) else '',
                'handle_start_date': wd[handle_start_idx] if handle_start_idx < len(wd) else '',
                'stage': stage,
                'score': round(min(1.0, score), 3),
            }
            if score > best_score:
                best_score = score
                best = cand

        elif handle_depth_pct < 5.0 and handle_days < 5:
            # Handle hasn't formed yet
            score = 0.35 + depth_score * 0.1 + symmetry * 0.1
            cand = {
                **default,
                'cup_depth_pct': round(cup_depth_pct, 2),
                'handle_depth_pct': round(handle_depth_pct, 2),
                'pivot_price': pivot_price,
                'cup_days': cup_days,
                'handle_days': handle_days,
                'cup_start_date': wd[left_rim_idx] if left_rim_idx < len(wd) else '',
                'handle_start_date': wd[handle_start_idx] if handle_start_idx < len(wd) else '',
                'stage': 'handle_forming',
                'score': round(score, 3),
            }
            if score > best_score:
                best_score = score
                best = cand

        elif handle_depth_pct > 15.0:
            # Handle too deep
            continue

        else:
            # Handle forming but outside valid day range
            score = 0.3 + depth_score * 0.1 + symmetry * 0.1
            cand = {
                **default,
                'cup_depth_pct': round(cup_depth_pct, 2),
                'handle_depth_pct': round(handle_depth_pct, 2),
                'pivot_price': pivot_price,
                'cup_days': cup_days,
                'handle_days': handle_days,
                'cup_start_date': wd[left_rim_idx] if left_rim_idx < len(wd) else '',
                'handle_start_date': wd[handle_start_idx] if handle_start_idx < len(wd) else '',
                'stage': 'handle_forming',
                'score': round(score, 3),
            }
            if score > best_score:
                best_score = score
                best = cand

    return best if best is not None else default
