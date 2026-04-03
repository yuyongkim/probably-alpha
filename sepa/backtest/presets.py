"""Market Wizards trader presets for backtesting.

Each preset is a StrategyConfig that reflects the trader's philosophy.
"""
from __future__ import annotations

from sepa.backtest.strategy import StrategyConfig

PRESETS: dict[str, StrategyConfig] = {
    'minervini': StrategyConfig(
        name='Minervini SEPA',
        description='Trend Template 5/8 + RS 상위. SEPA의 핵심 전략.',
        family='growth_momentum',
        min_tt_pass=5, rs_threshold=70.0,
        require_ma50=True, require_close_gt_sma200=True,
        require_near_52w_high=True, near_52w_threshold=0.75,
        max_positions=5, stop_loss_pct=0.075, sector_limit=2,
        rebalance='weekly',
    ),
    'oneil': StrategyConfig(
        name="O'Neil CAN SLIM",
        description='RS 최상위 + 실적 가속 + 신고가 돌파. 엄격한 손절.',
        family='growth_momentum',
        min_tt_pass=6, rs_threshold=80.0,
        require_ma50=True, require_close_gt_sma200=True,
        require_volume_expansion=True, min_volume_ratio=1.5,
        require_near_52w_high=True, near_52w_threshold=0.85,
        max_positions=4, stop_loss_pct=0.07, sector_limit=2, top_sectors=3,
        rebalance='weekly',
    ),
    'dennis': StrategyConfig(
        name='Dennis 터틀 시스템',
        description='20일 채널 돌파 + 거래량 확인. 추세추종의 원조.',
        family='trend_following',
        min_tt_pass=4, rs_threshold=50.0,
        require_ma50=True, require_close_gt_sma200=False,
        require_20d_breakout=True,
        require_volume_expansion=True, min_volume_ratio=1.3,
        sector_filter=False,
        max_positions=5, stop_loss_pct=0.08,
        rebalance='weekly',
    ),
    'seykota': StrategyConfig(
        name='Seykota 시스템 추세',
        description='추세 정배열만 따라가고, 규칙을 절대 어기지 않는다.',
        family='trend_following',
        min_tt_pass=7, rs_threshold=60.0,
        require_ma50=True, require_close_gt_sma200=True,
        sector_filter=False,
        max_positions=4, stop_loss_pct=0.08,
        rebalance='weekly',
    ),
    'hite': StrategyConfig(
        name='Hite 1% 리스크 룰',
        description='한 종목당 최대 손실 1%. 작게 잃고, 크게 벌기.',
        family='trend_following',
        min_tt_pass=5, rs_threshold=50.0,
        require_ma50=True, require_close_gt_sma200=False,
        sector_filter=True, top_sectors=10, sector_limit=2,
        max_positions=5, stop_loss_pct=0.05,
        rebalance='weekly',
    ),
    'jones': StrategyConfig(
        name='Jones 200MA 필터',
        description='200일선 위에서만 투자. 방어적 포지션 관리. 매크로 중시.',
        family='trend_following',
        min_tt_pass=6, rs_threshold=60.0,
        require_ma50=True, require_close_gt_sma200=True,
        max_positions=4, stop_loss_pct=0.06,
        rebalance='weekly',
    ),
    'driehaus': StrategyConfig(
        name='Driehaus 실적 서프라이즈',
        description='RS 최상위 + 공격적 집중 투자. 적은 종목, 큰 베팅.',
        family='growth_momentum',
        min_tt_pass=5, rs_threshold=85.0,
        require_ma50=True, require_close_gt_sma200=True,
        require_volume_expansion=True, min_volume_ratio=1.5,
        require_near_52w_high=True, near_52w_threshold=0.90,
        sector_filter=True, top_sectors=3, sector_limit=2,
        max_positions=3, stop_loss_pct=0.10,
        rebalance='weekly',
    ),
    'schwartz': StrategyConfig(
        name='Schwartz 단기 스윙',
        description='MA 위에서만 진입, 빠른 손절, 일간 리밸런싱.',
        family='swing',
        min_tt_pass=4, rs_threshold=40.0,
        require_ma50=True, require_close_gt_sma200=False,
        require_volatility_contraction=True,
        sector_filter=False,
        max_positions=5, stop_loss_pct=0.05,
        rebalance='daily',
    ),
    'raschke': StrategyConfig(
        name='Raschke NR7 스윙',
        description='변동성 수축(NR7) + 좁은 레인지 돌파. 단기 모멘텀.',
        family='swing',
        min_tt_pass=4, rs_threshold=40.0,
        require_ma50=True, require_close_gt_sma200=False,
        require_volatility_contraction=True,
        sector_filter=False,
        max_positions=5, stop_loss_pct=0.04,
        rebalance='daily',
    ),
    'weinstein': StrategyConfig(
        name='Weinstein Stage 2',
        description='30주 MA 위 + 거래량 증가. Stage 2 상승 구간 종목만.',
        family='growth_momentum',
        min_tt_pass=5, rs_threshold=60.0,
        require_ma50=True, require_close_gt_sma200=True,
        require_near_52w_high=True, near_52w_threshold=0.80,
        require_volume_expansion=True, min_volume_ratio=1.2,
        max_positions=5, stop_loss_pct=0.08,
        rebalance='weekly',
    ),
}


def get_preset(name: str) -> StrategyConfig | None:
    return PRESETS.get(name)


# Mapping: preset id -> wizard index person id(s)
PRESET_PERSON_MAP: dict[str, list[str]] = {
    'minervini': ['mark-minervini'],
    'oneil': ['william-oneil', 'david-ryan'],
    'dennis': ['richard-dennis'],
    'seykota': ['ed-seykota'],
    'hite': ['larry-hite'],
    'jones': ['paul-tudor-jones'],
    'driehaus': ['richard-driehaus'],
    'schwartz': ['marty-schwartz'],
    'raschke': ['linda-raschke'],
    'weinstein': ['mark-weinstein'],
}

# Reverse mapping: person id -> preset id
PERSON_PRESET_MAP: dict[str, str] = {}
for _preset_id, _person_ids in PRESET_PERSON_MAP.items():
    for _pid in _person_ids:
        PERSON_PRESET_MAP[_pid] = _preset_id


def list_presets() -> list[dict]:
    return [
        {
            'id': k,
            'name': v.name,
            'description': v.description,
            'family': v.family,
            'person_ids': PRESET_PERSON_MAP.get(k, []),
            'params': {
                'min_tt_pass': v.min_tt_pass,
                'rs_threshold': v.rs_threshold,
                'max_positions': v.max_positions,
                'stop_loss_pct': v.stop_loss_pct,
                'rebalance': v.rebalance,
                'require_volume_expansion': v.require_volume_expansion,
                'require_near_52w_high': v.require_near_52w_high,
                'require_volatility_contraction': v.require_volatility_contraction,
                'require_20d_breakout': v.require_20d_breakout,
            },
        }
        for k, v in PRESETS.items()
    ]
