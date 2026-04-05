"""Strategy configuration for backtests.

5 strategy families, each with distinct parameters:

1. Growth/Momentum (Minervini, O'Neil, Driehaus)
   - TT alignment + RS ranking + EPS growth filter
2. Trend Following (Dennis, Seykota, Hite)
   - Channel breakout + ATR-based stops/sizing
3. Swing/Short-term (Schwartz, Raschke)
   - Short MA + volatility contraction + tight stops
4. Macro/Defensive (Jones, Dalio)
   - Market regime filter + dynamic cash allocation
5. Value (Greenblatt)
   - PER/PBR/EV_EBITDA screening, no TT
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StrategyConfig:
    name: str = 'Custom'
    description: str = ''
    family: str = ''  # growth_momentum, trend_following, swing, macro, value

    # ── Signal Type ──────────────────────────────────────────────
    signal_type: str = 'trend_template'
    # 'trend_template' — Minervini TT 8-check (default)
    # 'channel_breakout' — Dennis/Turtle Donchian channel
    # 'value_screen' — PER/PBR/ROE screen
    # 'swing' — Short MA + volatility contraction

    # ── Alpha — Trend Template (signal_type='trend_template') ────
    min_tt_pass: int = 5           # 8 checks, min pass count
    rs_threshold: float = 70.0     # RS percentile cutoff (0~100)
    c5_multiplier: float = 1.30    # above 52w low by this factor
    c6_multiplier: float = 0.75    # within this % of 52w high

    require_ma50: bool = True            # close > SMA50
    require_close_gt_sma200: bool = True # close > SMA200

    # ── Earnings / Fundamental Filter (O'Neil, Driehaus) ─────────
    use_earnings_filter: bool = False
    min_eps_growth_yoy: float = 25.0     # % — O'Neil wants 25%+
    min_revenue_growth_yoy: float = 15.0 # %
    require_eps_acceleration: bool = False  # current QoQ > previous QoQ
    min_roe: float = 0.0                 # minimum ROE (0 = disabled)

    # ── Channel Breakout (signal_type='channel_breakout') ────────
    channel_entry_period: int = 20       # buy at N-day high (Dennis: 20 or 55)
    channel_exit_period: int = 10        # sell at N-day low
    require_channel_volume: bool = True  # volume surge on breakout

    # ── Value Screen (signal_type='value_screen') ────────────────
    max_per: float = 15.0
    max_pbr: float = 1.5
    min_roe_value: float = 15.0
    max_debt_ratio: float = 100.0

    # ── Entry Conditions ─────────────────────────────────────────
    require_volume_expansion: bool = False
    min_volume_ratio: float = 1.5        # vol_short / vol_long threshold
    require_near_52w_high: bool = False
    near_52w_threshold: float = 0.85     # close >= high52 * this
    require_volatility_contraction: bool = False  # ATR10 < ATR50
    require_20d_breakout: bool = False

    # ── Market Regime Filter (Jones, Dalio) ──────────────────────
    use_market_filter: bool = False
    market_ma_period: int = 200          # index MA period
    cash_in_bear_pct: float = 1.0        # 1.0 = 100% cash when bearish
    # 0.5 = 50% cash, 0.0 = ignore market regime

    # ── Sector Constraints ───────────────────────────────────────
    sector_filter: bool = True
    top_sectors: int = 5
    sector_limit: int = 3               # max positions per sector

    # ── Position Sizing ──────────────────────────────────────────
    sizing_method: str = 'equal_weight'
    # 'equal_weight' — divide cash equally among max_positions
    # 'atr_risk' — size based on ATR, risk_per_trade_pct of equity
    # 'kelly' — Kelly criterion (requires win_rate estimate)
    risk_per_trade_pct: float = 0.01     # 1% of equity risked per trade
    atr_period: int = 14                 # ATR lookback

    # ── Portfolio ────────────────────────────────────────────────
    initial_cash: int = 100_000_000
    max_positions: int = 5

    # ── Stop / Exit ──────────────────────────────────────────────
    stop_type: str = 'fixed_pct'
    # 'fixed_pct' — fixed % below entry (default)
    # 'atr_trailing' — N * ATR trailing stop
    # 'ma_trailing' — exit when close < N-day MA
    # 'channel_exit' — exit at channel_exit_period-day low
    stop_loss_pct: float = 0.075         # for fixed_pct
    atr_stop_multiplier: float = 2.0     # for atr_trailing
    ma_exit_period: int = 20             # for ma_trailing

    trailing_stop: bool = False
    trailing_start_pct: float = 0.10     # start trailing after 10% gain
    trailing_distance_pct: float = 0.05  # trail by 5%

    profit_target_pct: float = 0.0       # 0 = no target (let winners run)
    # nonzero = take profit at this % (for swing)

    # ── Rebalancing ──────────────────────────────────────────────
    rebalance: str = 'weekly'
    # 'daily', 'weekly', 'biweekly', 'monthly'
    partial_rebalance: bool = False
    # True = only exit losers/non-signals, keep winners
    # False = full rebalance (sell all, rebuy top signals)

    # ── Legacy compat ────────────────────────────────────────────
    sector_exit: bool = True
    leader_exit: bool = True
