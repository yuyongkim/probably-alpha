"""Chart pattern detection (Cup-with-Handle, etc.)."""
from __future__ import annotations


def detect_cup_with_handle(price_series: list[dict], min_cup_days: int = 30, max_cup_days: int = 150) -> dict:
    """Detect a Cup-with-Handle (CWH) chart pattern.

    Looks for a U-shaped cup formation followed by a small handle pullback.
    Cup depth: 15-35% from the left rim.
    Handle depth: 5-15% from the right rim.
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
    }

    closes = [float(row.get('close', 0.0)) for row in price_series if row.get('close', 0.0) > 0]
    dates = [str(row.get('date', '')) for row in price_series if row.get('close', 0.0) > 0]

    if len(closes) < min_cup_days + 10:
        return default

    # Use a lookback window of max_cup_days + 30 (handle room)
    lookback = min(len(closes), max_cup_days + 30)
    window_closes = closes[-lookback:]
    window_dates = dates[-lookback:]

    # Step 1: Find the left rim — highest point in the lookback window
    left_rim_idx = 0
    left_rim_price = window_closes[0]
    for i in range(len(window_closes)):
        if window_closes[i] > left_rim_price:
            left_rim_price = window_closes[i]
            left_rim_idx = i

    if left_rim_price <= 0:
        return default

    # Step 2: Find the cup bottom — lowest point after left rim
    search_end = min(len(window_closes), left_rim_idx + max_cup_days + 1)
    if left_rim_idx + 5 >= search_end:
        return default

    cup_bottom_idx = left_rim_idx + 1
    cup_bottom_price = window_closes[left_rim_idx + 1]
    for i in range(left_rim_idx + 1, search_end):
        if window_closes[i] < cup_bottom_price:
            cup_bottom_price = window_closes[i]
            cup_bottom_idx = i

    # Cup depth check: 15-35%
    cup_depth_pct = ((left_rim_price - cup_bottom_price) / left_rim_price) * 100.0
    if cup_depth_pct < 15.0 or cup_depth_pct > 35.0:
        # Cup depth outside acceptable range — check if still forming
        if cup_depth_pct >= 10.0 and cup_depth_pct < 15.0:
            # Shallow cup still forming
            return {
                **default,
                'cup_depth_pct': round(cup_depth_pct, 2),
                'cup_days': cup_bottom_idx - left_rim_idx,
                'cup_start_date': window_dates[left_rim_idx] if left_rim_idx < len(window_dates) else '',
                'stage': 'cup_forming',
            }
        return default

    # Step 3: Find the right rim — price recovery after cup bottom
    # Look for the point where price recovers to within 10% of the left rim
    right_rim_idx = None
    right_rim_price = 0.0
    for i in range(cup_bottom_idx + 1, len(window_closes)):
        if window_closes[i] >= left_rim_price * 0.90:
            right_rim_idx = i
            right_rim_price = window_closes[i]
            break

    cup_days = (right_rim_idx - left_rim_idx) if right_rim_idx is not None else (cup_bottom_idx - left_rim_idx)

    if right_rim_idx is None:
        # Cup bottom found but price hasn't recovered — cup still forming
        # Check if price is rising from the bottom (trending up in last 10 bars)
        recent_slice = window_closes[max(cup_bottom_idx, len(window_closes) - 10):]
        if len(recent_slice) >= 3 and recent_slice[-1] > recent_slice[0]:
            stage = 'cup_forming'
        else:
            stage = 'none'
        return {
            **default,
            'cup_depth_pct': round(cup_depth_pct, 2),
            'cup_days': cup_bottom_idx - left_rim_idx,
            'cup_start_date': window_dates[left_rim_idx] if left_rim_idx < len(window_dates) else '',
            'stage': stage,
        }

    # Validate cup duration
    if cup_days < min_cup_days or cup_days > max_cup_days:
        return default

    # Step 4: After the right rim, look for the handle (small pullback)
    remaining = len(window_closes) - right_rim_idx - 1

    if remaining < 2:
        # Right rim just formed, handle hasn't started
        return {
            **default,
            'cup_depth_pct': round(cup_depth_pct, 2),
            'cup_days': cup_days,
            'cup_start_date': window_dates[left_rim_idx] if left_rim_idx < len(window_dates) else '',
            'stage': 'cup_forming',
        }

    # Find handle high (start of handle pullback) and handle low
    handle_start_idx = right_rim_idx
    handle_high = right_rim_price

    # Look for the highest point around the right rim area as handle start
    handle_search_end = min(len(window_closes), right_rim_idx + 26)
    for i in range(right_rim_idx, handle_search_end):
        if window_closes[i] > handle_high:
            handle_high = window_closes[i]
            handle_start_idx = i

    # Find the handle low after handle start
    handle_low = handle_high
    handle_low_idx = handle_start_idx
    for i in range(handle_start_idx, len(window_closes)):
        if window_closes[i] < handle_low:
            handle_low = window_closes[i]
            handle_low_idx = i

    handle_depth_pct = ((handle_high - handle_low) / handle_high) * 100.0 if handle_high > 0 else 0.0
    handle_days = len(window_closes) - 1 - handle_start_idx

    # The pivot (buy point) is just above the handle high
    pivot_price = round(handle_high * 1.005, 2)

    # Determine stage
    if 5.0 <= handle_depth_pct <= 15.0 and 5 <= handle_days <= 25:
        # Valid handle exists
        current_price = window_closes[-1]
        if current_price >= handle_high * 0.995:
            stage = 'breakout_ready'
        else:
            stage = 'handle_forming'
        return {
            'detected': True,
            'cup_depth_pct': round(cup_depth_pct, 2),
            'handle_depth_pct': round(handle_depth_pct, 2),
            'pivot_price': pivot_price,
            'cup_days': cup_days,
            'handle_days': handle_days,
            'cup_start_date': window_dates[left_rim_idx] if left_rim_idx < len(window_dates) else '',
            'handle_start_date': window_dates[handle_start_idx] if handle_start_idx < len(window_dates) else '',
            'stage': stage,
        }
    elif handle_depth_pct < 5.0 and handle_days < 5:
        # Handle hasn't formed yet or too shallow
        return {
            **default,
            'cup_depth_pct': round(cup_depth_pct, 2),
            'handle_depth_pct': round(handle_depth_pct, 2),
            'pivot_price': pivot_price,
            'cup_days': cup_days,
            'handle_days': handle_days,
            'cup_start_date': window_dates[left_rim_idx] if left_rim_idx < len(window_dates) else '',
            'handle_start_date': window_dates[handle_start_idx] if handle_start_idx < len(window_dates) else '',
            'stage': 'handle_forming',
        }
    elif handle_depth_pct > 15.0:
        # Handle too deep — not a valid CWH
        return {
            **default,
            'cup_depth_pct': round(cup_depth_pct, 2),
            'handle_depth_pct': round(handle_depth_pct, 2),
            'cup_days': cup_days,
            'handle_days': handle_days,
            'cup_start_date': window_dates[left_rim_idx] if left_rim_idx < len(window_dates) else '',
            'stage': 'none',
        }
    else:
        # Handle forming but not yet within valid day range
        return {
            **default,
            'cup_depth_pct': round(cup_depth_pct, 2),
            'handle_depth_pct': round(handle_depth_pct, 2),
            'pivot_price': pivot_price,
            'cup_days': cup_days,
            'handle_days': handle_days,
            'cup_start_date': window_dates[left_rim_idx] if left_rim_idx < len(window_dates) else '',
            'handle_start_date': window_dates[handle_start_idx] if handle_start_idx < len(window_dates) else '',
            'stage': 'handle_forming',
        }
