"""Market Wizards trader presets for backtesting.

Each preset reflects the actual trading philosophy, not just TT parameter tweaks.
"""
from __future__ import annotations

from sepa.backtest.strategy import StrategyConfig

PRESETS: dict[str, StrategyConfig] = {

    # ━━ Growth / Momentum ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    'minervini': StrategyConfig(
        name='Minervini SEPA',
        description='Trend Template 5/8 + RS 상위 + VCP 수축',
        family='growth_momentum',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=70.0,
        require_ma50=True, require_close_gt_sma200=True,
        require_near_52w_high=True, near_52w_threshold=0.75,
        require_volatility_contraction=True,
        use_earnings_filter=True,
        min_eps_growth_yoy=25.0,
        max_positions=5, stop_loss_pct=0.075, sector_limit=2,
        stop_type='fixed_pct',
        trailing_stop=True, trailing_start_pct=0.15, trailing_distance_pct=0.08,
        rebalance='weekly',
    ),

    'oneil': StrategyConfig(
        name="O'Neil CAN SLIM",
        description='EPS 가속 + RS 최상위 + 거래량 돌파 + 엄격 손절',
        family='growth_momentum',
        signal_type='trend_template',
        min_tt_pass=6, rs_threshold=80.0,
        require_ma50=True, require_close_gt_sma200=True,
        require_volume_expansion=True, min_volume_ratio=1.5,
        require_near_52w_high=True, near_52w_threshold=0.85,
        use_earnings_filter=True,
        min_eps_growth_yoy=25.0,
        min_revenue_growth_yoy=20.0,
        require_eps_acceleration=True,
        max_positions=4, stop_loss_pct=0.07, sector_limit=2, top_sectors=3,
        stop_type='fixed_pct',
        rebalance='weekly',
    ),

    'driehaus': StrategyConfig(
        name='Driehaus 모멘텀',
        description='RS 최상위 + 실적 서프라이즈 + 집중 투자',
        family='growth_momentum',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=85.0,
        require_ma50=True, require_close_gt_sma200=True,
        require_volume_expansion=True, min_volume_ratio=1.5,
        require_near_52w_high=True, near_52w_threshold=0.90,
        use_earnings_filter=True,
        min_eps_growth_yoy=20.0,
        sector_filter=True, top_sectors=3, sector_limit=2,
        max_positions=3, stop_loss_pct=0.10,
        stop_type='fixed_pct',
        trailing_stop=True, trailing_start_pct=0.20, trailing_distance_pct=0.10,
        rebalance='weekly',
    ),

    'weinstein': StrategyConfig(
        name='Weinstein Stage 2',
        description='30주 MA 위 + 거래량 증가 + Stage 2 상승 구간',
        family='growth_momentum',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=60.0,
        require_ma50=True, require_close_gt_sma200=True,
        require_near_52w_high=True, near_52w_threshold=0.80,
        require_volume_expansion=True, min_volume_ratio=1.2,
        max_positions=5, stop_loss_pct=0.08,
        stop_type='ma_trailing', ma_exit_period=150,  # exit below 30-week MA
        rebalance='weekly',
    ),

    # ━━ Trend Following ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    'dennis': StrategyConfig(
        name='Dennis 터틀',
        description='55일 채널 돌파 + ATR 손절/사이징 + 주간 리밸런스',
        family='trend_following',
        signal_type='channel_breakout',
        channel_entry_period=55,  # 55-day breakout (System 2)
        channel_exit_period=20,   # 20-day low exit
        require_channel_volume=True,
        sizing_method='atr_risk',
        risk_per_trade_pct=0.01,
        atr_period=20,
        stop_type='atr_trailing', atr_stop_multiplier=2.0,
        sector_filter=False,
        max_positions=6, rebalance='weekly',  # weekly, not daily
        partial_rebalance=True,  # keep winners
    ),

    'seykota': StrategyConfig(
        name='Seykota 시스템',
        description='강한 추세만 추종 + 절대 규칙 준수',
        family='trend_following',
        signal_type='trend_template',
        min_tt_pass=7, rs_threshold=60.0,
        require_ma50=True, require_close_gt_sma200=True,
        sizing_method='atr_risk',
        risk_per_trade_pct=0.01,
        stop_type='atr_trailing', atr_stop_multiplier=3.0,
        sector_filter=False,
        max_positions=4, rebalance='weekly',
    ),

    'hite': StrategyConfig(
        name='Hite 1% 리스크',
        description='종목당 최대 손실 1% + 분산 포트폴리오',
        family='trend_following',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=50.0,
        require_ma50=True,
        sizing_method='atr_risk',
        risk_per_trade_pct=0.01,  # strict 1% rule
        atr_period=14,
        stop_type='atr_trailing', atr_stop_multiplier=2.0,
        sector_filter=True, top_sectors=10, sector_limit=2,
        max_positions=10, rebalance='weekly',
    ),

    # ━━ Swing / Short-term ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    'schwartz': StrategyConfig(
        name='Schwartz 단기 스윙',
        description='10MA 위 진입 + 빠른 손절 + 일간 리밸런싱',
        family='swing',
        signal_type='swing',
        min_tt_pass=4, rs_threshold=40.0,
        require_ma50=True,
        require_volatility_contraction=True,
        stop_type='fixed_pct', stop_loss_pct=0.04,
        profit_target_pct=0.08,  # 8% profit target
        sector_filter=False,
        max_positions=5, rebalance='daily',
    ),

    'raschke': StrategyConfig(
        name='Raschke NR7 스윙',
        description='변동성 수축 + 레인지 돌파 + 단기 모멘텀',
        family='swing',
        signal_type='swing',
        min_tt_pass=4, rs_threshold=40.0,
        require_ma50=True,
        require_volatility_contraction=True,
        require_20d_breakout=True,
        stop_type='fixed_pct', stop_loss_pct=0.03,
        profit_target_pct=0.06,
        sector_filter=False,
        max_positions=5, rebalance='daily',
    ),

    # ━━ Macro / Defensive ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    'jones': StrategyConfig(
        name='Jones 매크로',
        description='시장 200MA 필터 + 약세장 현금 비중 확대',
        family='macro',
        signal_type='trend_template',
        min_tt_pass=6, rs_threshold=60.0,
        require_ma50=True, require_close_gt_sma200=True,
        use_market_filter=True,
        market_ma_period=200,
        cash_in_bear_pct=1.0,  # 100% cash when KOSPI < 200MA
        max_positions=4, stop_loss_pct=0.06,
        stop_type='fixed_pct',
        trailing_stop=True, trailing_start_pct=0.10, trailing_distance_pct=0.05,
        rebalance='weekly',
    ),

    'dalio': StrategyConfig(
        name='Dalio 올웨더',
        description='시장 상태에 따라 공격/방어 전환',
        family='macro',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=50.0,
        use_market_filter=True,
        market_ma_period=200,
        cash_in_bear_pct=0.5,  # 50% cash in bear market
        sector_filter=True, top_sectors=7,
        max_positions=8, stop_loss_pct=0.10,
        stop_type='ma_trailing', ma_exit_period=50,
        rebalance='monthly',
        partial_rebalance=True,
    ),

    # ━━ Value ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    'greenblatt': StrategyConfig(
        name='Greenblatt 마법공식',
        description='저PER + 고ROE 조합 (Magic Formula)',
        family='value',
        signal_type='value_screen',
        max_per=15.0,
        max_pbr=1.5,
        min_roe_value=15.0,
        max_debt_ratio=100.0,
        sector_filter=False,
        max_positions=10, stop_loss_pct=0.15,
        stop_type='fixed_pct',
        rebalance='monthly',
        partial_rebalance=True,
    ),
    # ━━ Additional Clusters ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    'druckenmiller': StrategyConfig(
        name='Druckenmiller 매크로집중',
        description='확신 있을 때 크게 베팅. 매크로 방향 확인 후 집중 투자.',
        family='macro',
        signal_type='trend_template',
        min_tt_pass=6, rs_threshold=70.0,
        require_ma50=True, require_close_gt_sma200=True,
        use_market_filter=True, market_ma_period=200,
        cash_in_bear_pct=1.0,
        max_positions=3, stop_loss_pct=0.10,
        stop_type='fixed_pct',
        trailing_stop=True, trailing_start_pct=0.15, trailing_distance_pct=0.08,
        rebalance='weekly',
    ),

    'kovner': StrategyConfig(
        name='Kovner 글로벌매크로',
        description='금리/환율/원자재 방향성 + 추세 확인 후 진입.',
        family='macro',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=55.0,
        use_market_filter=True, market_ma_period=200,
        cash_in_bear_pct=0.7,
        sector_filter=True, top_sectors=7,
        max_positions=6, stop_loss_pct=0.08,
        stop_type='fixed_pct',
        rebalance='weekly', partial_rebalance=True,
    ),

    'livermore': StrategyConfig(
        name='Livermore 피라미딩',
        description='추세 확인 후 추가 매수. 신고가 돌파 시 집중.',
        family='growth_momentum',
        signal_type='trend_template',
        min_tt_pass=6, rs_threshold=75.0,
        require_ma50=True, require_close_gt_sma200=True,
        require_near_52w_high=True, near_52w_threshold=0.90,
        max_positions=4, stop_loss_pct=0.10,
        stop_type='fixed_pct',
        trailing_stop=True, trailing_start_pct=0.10, trailing_distance_pct=0.07,
        rebalance='weekly',
    ),

    'darvas': StrategyConfig(
        name='Darvas 박스이론',
        description='박스 상단 돌파 + 거래량 확인. 52주 고점 근처 종목만.',
        family='growth_momentum',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=65.0,
        require_ma50=True,
        require_near_52w_high=True, near_52w_threshold=0.85,
        require_volume_expansion=True, min_volume_ratio=1.3,
        max_positions=5, stop_loss_pct=0.08,
        stop_type='fixed_pct',
        rebalance='weekly',
    ),

    'cohen': StrategyConfig(
        name='Cohen 빠른실행',
        description='빠른 판단 + 적극적 사이징. RS 최상위 종목 집중.',
        family='growth_momentum',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=80.0,
        require_ma50=True,
        max_positions=5, stop_loss_pct=0.06,
        stop_type='fixed_pct',
        rebalance='daily',
    ),

    'steinhardt': StrategyConfig(
        name='Steinhardt 역발상',
        description='시장과 반대로. 저평가 대형주 + 촉매 기대.',
        family='value',
        signal_type='value_screen',
        max_per=12.0, max_pbr=1.2, min_roe_value=12.0, max_debt_ratio=80.0,
        sector_filter=False,
        max_positions=8, stop_loss_pct=0.12,
        stop_type='fixed_pct',
        rebalance='monthly', partial_rebalance=True,
    ),

    'thorp': StrategyConfig(
        name='Thorp 확률/퀀트',
        description='확률적 우위(edge) 확인 후 켈리 기준 베팅.',
        family='trend_following',
        signal_type='trend_template',
        min_tt_pass=6, rs_threshold=60.0,
        sizing_method='atr_risk',
        risk_per_trade_pct=0.015,
        atr_period=14,
        stop_type='atr_trailing', atr_stop_multiplier=2.5,
        sector_filter=True, top_sectors=7,
        max_positions=8, rebalance='weekly',
    ),

    'brandt': StrategyConfig(
        name='Brandt 차트/리스크',
        description='클래식 차트 패턴 + 엄격한 리스크 관리.',
        family='trend_following',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=55.0,
        require_ma50=True,
        require_volatility_contraction=True,
        sizing_method='atr_risk',
        risk_per_trade_pct=0.01,
        stop_type='atr_trailing', atr_stop_multiplier=2.0,
        max_positions=6, rebalance='weekly',
    ),

    'okumus': StrategyConfig(
        name='Okumus 집중성장',
        description='소수 고확신 성장주에 집중. EPS 가속 + RS 최상위.',
        family='growth_momentum',
        signal_type='trend_template',
        min_tt_pass=6, rs_threshold=85.0,
        use_earnings_filter=True,
        min_eps_growth_yoy=20.0,
        max_positions=3, stop_loss_pct=0.10,
        stop_type='fixed_pct',
        trailing_stop=True, trailing_start_pct=0.20, trailing_distance_pct=0.10,
        rebalance='weekly',
    ),

    'galante': StrategyConfig(
        name='Galante 롱숏밸런스',
        description='롱 포지션 방어적 관리. 균형 잡힌 포트폴리오.',
        family='trend_following',
        signal_type='trend_template',
        min_tt_pass=5, rs_threshold=50.0,
        use_market_filter=True, market_ma_period=200,
        cash_in_bear_pct=0.5,
        sector_filter=True, top_sectors=7, sector_limit=2,
        max_positions=8, stop_loss_pct=0.06,
        stop_type='fixed_pct',
        rebalance='weekly', partial_rebalance=True,
    ),

    'shapiro': StrategyConfig(
        name='Shapiro 역발상매크로',
        description='군중과 반대 방향. 극단적 센티먼트에서 진입.',
        family='macro',
        signal_type='trend_template',
        min_tt_pass=4, rs_threshold=40.0,
        use_market_filter=True, market_ma_period=200,
        cash_in_bear_pct=0.3,  # 약세장에서도 30% 투자
        sector_filter=False,
        max_positions=6, stop_loss_pct=0.12,
        stop_type='fixed_pct',
        rebalance='biweekly',
    ),

    'bielfeldt': StrategyConfig(
        name='Bielfeldt 인내집중',
        description='잘 아는 시장 하나에 집중. 확인될 때까지 기다림.',
        family='trend_following',
        signal_type='trend_template',
        min_tt_pass=7, rs_threshold=70.0,
        require_ma50=True, require_close_gt_sma200=True,
        sector_filter=True, top_sectors=3, sector_limit=2,
        max_positions=3, stop_loss_pct=0.08,
        stop_type='fixed_pct',
        trailing_stop=True, trailing_start_pct=0.12, trailing_distance_pct=0.06,
        rebalance='weekly',
    ),

    'blake': StrategyConfig(
        name='Blake 스윙모멘텀',
        description='단기 모멘텀 + 자금 흐름 포착. 빠른 순환.',
        family='swing',
        signal_type='swing',
        min_tt_pass=4, rs_threshold=50.0,
        require_ma50=True,
        require_20d_breakout=True,
        stop_type='fixed_pct', stop_loss_pct=0.05,
        profit_target_pct=0.10,
        sector_filter=False,
        max_positions=6, rebalance='daily',
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
    'dalio': ['ray-dalio'],
    'driehaus': ['richard-driehaus'],
    'schwartz': ['marty-schwartz'],
    'raschke': ['linda-bradford-raschke'],
    'weinstein': ['mark-weinstein'],
    'greenblatt': ['joel-greenblatt'],
    'druckenmiller': ['stanley-druckenmiller'],
    'kovner': ['bruce-kovner'],
    'livermore': ['jesse-livermore'],
    'darvas': ['nicolas-darvas'],
    'cohen': ['steve-cohen'],
    'steinhardt': ['michael-steinhardt'],
    'thorp': ['edward-thorp'],
    'brandt': ['peter-brandt'],
    'okumus': ['ahmet-okumus'],
    'galante': ['dana-galante'],
    'shapiro': ['jason-shapiro'],
    'bielfeldt': ['gary-bielfeldt'],
    'blake': ['gil-blake'],
}

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
            'signal_type': v.signal_type,
            'person_ids': PRESET_PERSON_MAP.get(k, []),
            'params': {
                'signal_type': v.signal_type,
                'min_tt_pass': v.min_tt_pass,
                'rs_threshold': v.rs_threshold,
                'max_positions': v.max_positions,
                'stop_loss_pct': v.stop_loss_pct,
                'stop_type': v.stop_type,
                'sizing_method': v.sizing_method,
                'rebalance': v.rebalance,
                'use_earnings_filter': v.use_earnings_filter,
                'use_market_filter': v.use_market_filter,
            },
        }
        for k, v in PRESETS.items()
    ]
