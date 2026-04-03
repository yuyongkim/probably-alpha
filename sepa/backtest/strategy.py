"""Strategy configuration for backtests.

Each StrategyConfig defines the complete rule set for a trader's philosophy:
- Alpha screening parameters (what to buy)
- Extra entry conditions (volume, VCP, breakout)
- Portfolio/risk parameters (how much, when to sell)
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StrategyConfig:
    name: str = 'Custom'
    description: str = ''
    family: str = ''  # trend_following, growth_momentum, swing, etc.

    # Alpha — Trend Template params
    min_tt_pass: int = 5           # 8조건 중 최소 통과 수
    rs_threshold: float = 70.0     # RS 백분위 임계값 (0~100)
    c5_multiplier: float = 1.30    # 52주 저점 대비 배수
    c6_multiplier: float = 0.75    # 52주 고점 대비 배수

    # Alpha — Hard gates
    require_ma50: bool = True            # close > SMA50 필수
    require_close_gt_sma200: bool = True # close > SMA200 필수

    # Extra entry conditions (wizard-style)
    require_volume_expansion: bool = False     # vol_5d > vol_50d * min_volume_ratio
    min_volume_ratio: float = 1.5             # 거래량 팽창 최소 배수
    require_near_52w_high: bool = False       # close >= high52 * 0.85
    near_52w_threshold: float = 0.85          # 52주 고점 근접 임계값
    require_volatility_contraction: bool = False  # ATR10 < ATR50 (VCP)
    require_20d_breakout: bool = False        # close >= 20일 최고가

    # Sector constraints
    sector_filter: bool = True     # 상위 N섹터만
    top_sectors: int = 5
    sector_limit: int = 3          # 섹터당 최대 종목

    # Portfolio / Risk
    initial_cash: int = 100_000_000
    max_positions: int = 5
    stop_loss_pct: float = 0.075   # 손절 비율
    rebalance: str = 'weekly'      # weekly or daily

    # Exit rules
    sector_exit: bool = True       # 섹터 이탈 시 청산
    leader_exit: bool = True       # 리더 이탈 시 청산
