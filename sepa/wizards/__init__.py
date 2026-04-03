"""Market Wizards — 시장의 마법사 전략 모듈.

Jack Schwager 3부작에 등장하는 22개 트레이더 전략을 코드로 구현.
각 전략은 StockData를 입력받아 WizardResult(통과/점수/조건별 결과)를 반환.

Usage:
    from sepa.wizards import WizardScreener, StockData

    screener = WizardScreener()  # 전체 전략
    result = screener.screen_stock(stock_data)

    # 카테고리별
    screener = WizardScreener(categories=['trend_following', 'growth_momentum'])

    # 특정 트레이더
    screener = WizardScreener(traders=['Mark Minervini', 'William O\\'Neil'])
"""

from sepa.wizards.base import StockData, WizardResult, ConditionResult, WizardStrategy
from sepa.wizards.screener import WizardScreener, ScreenResult, ALL_STRATEGIES

# Strategy modules
from sepa.wizards.trend_followers import (
    DennisTurtleSystem1,
    DennisTurtleSystem2,
    SeykotaTrend,
    JonesTrendFilter,
    HiteRiskTrend,
    BielfeldtConcentratedTrend,
    WeissLongTermTrend,
)
from sepa.wizards.growth_momentum import (
    ONeilCanSlim,
    RyanVcpGrowth,
    DriehausMomentum,
    WaltonStage2Entry,
    CohenEventMomentum,
)
from sepa.wizards.swing_traders import (
    SchwartzEma10,
    RaschkeNr7Breakout,
    SperandeoTrendReversal,
    TroutMeanReversion,
)
from sepa.wizards.contrarian_value import (
    RogersDeepValue,
    SteinhardtVariantPerception,
    OkumusDeepValueTurnaround,
    GalanteShortSetup,
)
from sepa.wizards.volatility_macro import (
    MinerviniTrendTemplate,
    MinerviniVcp,
    WeinsteinSqueeze,
    DruckenmillerMacroLiquidity,
    LipschutzRiskReward,
    BassoVolatilityFilter,
)

__all__ = [
    # Core
    'StockData',
    'WizardResult',
    'ConditionResult',
    'WizardStrategy',
    'WizardScreener',
    'ScreenResult',
    'ALL_STRATEGIES',
    # Trend Following
    'DennisTurtleSystem1',
    'DennisTurtleSystem2',
    'SeykotaTrend',
    'JonesTrendFilter',
    'HiteRiskTrend',
    'BielfeldtConcentratedTrend',
    'WeissLongTermTrend',
    # Growth Momentum
    'ONeilCanSlim',
    'RyanVcpGrowth',
    'DriehausMomentum',
    'WaltonStage2Entry',
    'CohenEventMomentum',
    # Swing
    'SchwartzEma10',
    'RaschkeNr7Breakout',
    'SperandeoTrendReversal',
    'TroutMeanReversion',
    # Contrarian / Value
    'RogersDeepValue',
    'SteinhardtVariantPerception',
    'OkumusDeepValueTurnaround',
    'GalanteShortSetup',
    # Volatility / Macro
    'MinerviniTrendTemplate',
    'MinerviniVcp',
    'WeinsteinSqueeze',
    'DruckenmillerMacroLiquidity',
    'LipschutzRiskReward',
    'BassoVolatilityFilter',
]
