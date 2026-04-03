from __future__ import annotations


def scoring_reference() -> dict:
    return {
        'philosophy': [
            'Minervini starts with relative strength. The stock should beat its benchmark before the breakout becomes obvious.',
            'True leader stocks usually come from true leader sectors. A strong single stock inside a weak group is not enough.',
            'Price structure, volume contraction/expansion, and EPS direction should line up before risk is committed.',
        ],
        'formulas': [
            {
                'id': 'sector_daily',
                'title': 'Leader Sector Score',
                'expression': 'leader_score = ((0.32 x sector_rs_pct) + (0.24 x alpha_ratio) + (0.14 x beta_ratio) + (0.18 x breakout_score) + (0.12 x volume_participation)) x breadth_multiplier x 100',
                'terms': [
                    'sector_rs_pct = 120-day sector return percentile / 100',
                    'alpha_ratio = alpha_count / universe_count',
                    'beta_ratio = beta_count / alpha_count',
                    'breakout_score = sector RS proximity to 120-day high, boosted when breakout is already in setup/confirmed state',
                    'volume_participation = average of member volume ratios scaled to a 0-1 range',
                    'breadth_multiplier = min(1, universe_count / 3)',
                ],
                'meaning': 'Sector ranking now rewards actual breadth and setup quality instead of letting single-stock groups dominate.',
                'minervini_link': 'Leadership should be visible in the group first, then in the stock.',
            },
            {
                'id': 'stock_daily',
                'title': 'Leader Stock Score',
                'expression': 'leader_stock_score = (0.43 x alpha_score) + (4.0 x beta_confidence) + (3.0 x gamma_score) + (0.10 x ret120_pct) + (0.25 x sector_leader_score)',
                'terms': [
                    'alpha_score = trend-template quality',
                    'beta_confidence = VCP and contraction quality',
                    'gamma_score = EPS and overlay quality',
                    'ret120_pct = 120-day return in percent',
                    'sector_leader_score = sector-level leadership score',
                ],
                'meaning': 'A stock inherits part of its rank from the sector. This prevents isolated names from appearing as true leaders too early.',
                'minervini_link': 'The best breakouts usually emerge from already-leading groups.',
            },
            {
                'id': 'rs_line',
                'title': 'Relative Strength Line',
                'expression': 'rs_line = 100 x (stock_base100 / index_base100)',
                'terms': [
                    'stock_base100 = stock rebased to 100 from the first visible bar',
                    'index_base100 = KOSPI or KOSDAQ rebased the same way',
                ],
                'meaning': 'This shows whether the stock is outperforming its own market benchmark, not just rising in absolute price.',
                'minervini_link': 'RS often turns up before price breaks out.',
            },
            {
                'id': 'volume_ratio',
                'title': 'Volume Ratio',
                'expression': 'volume_ratio_20 = today_volume / avg(volume, 20)',
                'terms': [
                    '< 0.8x = dry-up',
                    '1.0x = normal participation',
                    '> 1.5x = expansion',
                ],
                'meaning': 'Minervini wants quiet pullbacks and expanding volume on the move.',
                'minervini_link': 'Volume should contract inside the base and expand at the breakout.',
            },
            {
                'id': 'sector_breakout',
                'title': 'Sector Breakout State',
                'expression': 'confirmed if breadth >= 2 names and sector_rs >= 0.995 x high120 and volume_participation >= 0.72; setup if breadth >= 2 names and sector_rs >= 0.97 x high120 and volume_participation >= 0.45',
                'terms': [
                    'high120 = sector RS 120-day high',
                    'volume_participation = 0-1 participation score built from member volume ratios',
                ],
                'meaning': 'A sector should be close to a new RS high and show broad participation before it is treated as real leadership.',
                'minervini_link': 'Group confirmation matters. One stock is not a sector.',
            },
            {
                'id': 'recommendation',
                'title': 'Recommendation Score',
                'expression': 'recommendation_score = (0.45 x alpha) + (0.20 x beta x 10) + (0.20 x gamma x 10) + (0.10 x ret120_pct) + (0.05 x least_resistance_bonus)',
                'terms': [
                    'least_resistance_bonus = 100 for clear uptrend, otherwise distance-based discount',
                    'EPS gate must be positive_growth or strong_growth',
                    'least resistance gate must be up_least_resistance or pullback_in_uptrend',
                ],
                'meaning': 'Recommendation ranking is stricter than raw leadership ranking because it applies execution gates.',
                'minervini_link': 'Good structure without earnings support is not enough.',
            },
            {
                'id': 'persistence',
                'title': 'Leadership Persistence',
                'expression': 'persistence_score = 100 x (0.35 x appearance_ratio + 0.25 x current_streak_ratio + 0.20 x max_streak_ratio + 0.15 x rank_strength + 0.05 x top1_ratio)',
                'terms': [
                    'appearance_ratio = share of lookback bars spent inside the top-N',
                    'current_streak_ratio = current streak / lookback',
                    'max_streak_ratio = max streak / lookback',
                    'rank_strength = strength of average rank when present',
                    'top1_ratio = share of bars spent at rank 1',
                ],
                'meaning': 'This tells you whether the move is persistent leadership or just a temporary spike.',
                'minervini_link': 'Durable leaders tend to stay near the top, not just appear once.',
            },
        ],
        'usage': [
            'Use the sector heatmap first to see whether leadership is broad enough to trust.',
            'Then inspect the integrated chart: price, volume, RS, and MACD share the same time axis.',
            'Use historical date selection or backtest buckets to check whether the leadership held over time.',
        ],
    }
