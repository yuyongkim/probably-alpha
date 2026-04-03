"""Trend-following strategies from Market Wizards.

Traders: Richard Dennis, Ed Seykota, Paul Tudor Jones,
         Larry Hite, Gary Bielfeldt, Al Weiss
"""

from __future__ import annotations

from sepa.wizards.base import WizardStrategy, StockData, WizardResult, ConditionResult
from sepa.wizards import indicators as ind


# ===================================================================
# 1. Richard Dennis — Turtle Trading System 1 & 2
# ===================================================================

class DennisTurtleSystem1(WizardStrategy):
    name = 'Dennis Turtle System 1'
    trader = 'Richard Dennis'
    category = 'trend_following'
    book = 'MW1989'
    description_text = (
        '$400→$200M. 터틀 실험 창시자. 20일 고가 돌파 매수, 10일 저가 이탈 매도. '
        '"트레이딩은 가르칠 수 있다."'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, volumes = data.closes, data.highs, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: 현재가 >= 20일 최고가 (신고가 돌파)
        if len(highs) >= 20:
            high20 = max(highs[-20:])
            conds.append(self._cond(
                '현재가 >= 20일 최고가', data.close >= high20,
                f'{data.close:,.0f} vs {high20:,.0f}',
                '현재가 >= MAX(고가, 20)',
            ))
        else:
            conds.append(self._cond('현재가 >= 20일 최고가', False, '데이터 부족'))

        # 조건2: 거래량 >= 20일 평균거래량
        if len(volumes) >= 20:
            vol_avg = sum(volumes[-20:]) / 20
            conds.append(self._cond(
                '거래량 >= 20일 평균거래량', data.volume >= vol_avg,
                f'{data.volume:,.0f} vs {vol_avg:,.0f}',
                '거래량 >= 이동평균(거래량,20)',
            ))
        else:
            conds.append(self._cond('거래량 >= 20일 평균거래량', False, '데이터 부족'))

        # 조건3: 현재가 > 50일 이동평균 (중기 추세)
        if len(closes) >= 50:
            sma50 = sum(closes[-50:]) / 50
            conds.append(self._cond(
                '현재가 > SMA(50)', data.close > sma50,
                f'{data.close:,.0f} vs {sma50:,.0f}',
                '현재가 > 이동평균(종가,50)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(50)', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 >= MAX(고가, 20)',
            '거래량 >= 이동평균(거래량, 20)',
            '현재가 > 이동평균(종가, 50)',
        ]


class DennisTurtleSystem2(WizardStrategy):
    name = 'Dennis Turtle System 2'
    trader = 'Richard Dennis'
    category = 'trend_following'
    book = 'MW1989'
    description_text = '55일 고가 돌파 매수. 장기 추세추종. System 1보다 느리지만 큰 추세 포착.'

    def screen(self, data: StockData) -> WizardResult:
        closes, highs = data.closes, data.highs
        conds: list[ConditionResult] = []

        # 조건1: 현재가 >= 55일 최고가
        if len(highs) >= 55:
            high55 = max(highs[-55:])
            conds.append(self._cond(
                '현재가 >= 55일 최고가', data.close >= high55,
                f'{data.close:,.0f} vs {high55:,.0f}',
                '현재가 >= MAX(고가, 55)',
            ))
        else:
            conds.append(self._cond('현재가 >= 55일 최고가', False, '데이터 부족'))

        # 조건2: 현재가 > 120일 이동평균
        if len(closes) >= 120:
            sma120 = sum(closes[-120:]) / 120
            conds.append(self._cond(
                '현재가 > SMA(120)', data.close > sma120,
                f'{data.close:,.0f} vs {sma120:,.0f}',
                '현재가 > 이동평균(종가,120)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(120)', False, '데이터 부족'))

        # 조건3: 200일 이동평균 상승
        if len(closes) >= 222:
            sma200_now = sum(closes[-200:]) / 200
            sma200_ago = sum(closes[-222:-22]) / 200
            conds.append(self._cond(
                'SMA(200) 상승 중', sma200_now > sma200_ago,
                f'{sma200_now:,.0f} vs 22일전 {sma200_ago:,.0f}',
                '이동평균(종가,200) > 이동평균(종가,200)[22일전]',
            ))
        else:
            conds.append(self._cond('SMA(200) 상승 중', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 >= MAX(고가, 55)',
            '현재가 > 이동평균(종가, 120)',
            '이동평균(종가,200) > 이동평균(종가,200)[22일전]',
        ]


# ===================================================================
# 2. Ed Seykota — Trend Following + EMA Cross
# ===================================================================

class SeykotaTrend(WizardStrategy):
    name = 'Seykota Trend System'
    trader = 'Ed Seykota'
    category = 'trend_following'
    book = 'MW1989'
    description_text = (
        'MIT 전기공학. 최초 컴퓨터 트레이딩. 12년 250,000% 수익. '
        '"추세는 친구다 — 끝날 때까지." 장기 EMA + 골든크로스.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes = data.closes
        conds: list[ConditionResult] = []

        # 조건1: EMA(12) > EMA(26)
        if len(closes) >= 26:
            ema12 = ind.ema(closes, 12)
            ema26 = ind.ema(closes, 26)
            conds.append(self._cond(
                'EMA(12) > EMA(26)', ema12[-1] > ema26[-1],
                f'{ema12[-1]:,.0f} vs {ema26[-1]:,.0f}',
                'EMA(12) > EMA(26)',
            ))
        else:
            conds.append(self._cond('EMA(12) > EMA(26)', False, '데이터 부족'))

        # 조건2: 현재가 > SMA(200)
        if len(closes) >= 200:
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                '현재가 > SMA(200)', data.close > sma200,
                f'{data.close:,.0f} vs {sma200:,.0f}',
                '현재가 > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(200)', False, '데이터 부족'))

        # 조건3: SMA(50) > SMA(200) — 골든크로스 유지
        if len(closes) >= 200:
            sma50 = sum(closes[-50:]) / 50
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                'SMA(50) > SMA(200) 골든크로스', sma50 > sma200,
                f'{sma50:,.0f} vs {sma200:,.0f}',
                '이동평균(종가,50) > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('SMA(50) > SMA(200)', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            'EMA(12) > EMA(26)',
            '현재가 > 이동평균(종가,200)',
            '이동평균(종가,50) > 이동평균(종가,200)',
        ]


# ===================================================================
# 3. Paul Tudor Jones — 200MA Filter
# ===================================================================

class JonesTrendFilter(WizardStrategy):
    name = 'Jones 200MA Trend Filter'
    trader = 'Paul Tudor Jones'
    category = 'trend_following'
    book = 'MW1989'
    description_text = (
        '1987년 블랙먼데이 200% 수익. "먼저 방어, 그다음 공격." '
        '200일 이동평균이 핵심 필터. 200MA 아래면 매수 금지.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes = data.closes
        conds: list[ConditionResult] = []

        # 조건1: 현재가 > SMA(200)
        if len(closes) >= 200:
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                '현재가 > SMA(200)', data.close > sma200,
                f'{data.close:,.0f} vs {sma200:,.0f}',
                '현재가 > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(200)', False, '데이터 부족'))

        # 조건2: SMA(200) 기울기 양 (5일전 대비)
        if len(closes) >= 205:
            sma200_now = sum(closes[-200:]) / 200
            sma200_5ago = sum(closes[-205:-5]) / 200
            conds.append(self._cond(
                'SMA(200) 상승 기울기', sma200_now > sma200_5ago,
                f'{sma200_now:,.0f} vs 5일전 {sma200_5ago:,.0f}',
                '이동평균(종가,200) > 이동평균(종가,200)[5일전]',
            ))
        else:
            conds.append(self._cond('SMA(200) 상승 기울기', False, '데이터 부족'))

        # 조건3: 5일 등락률 > -3% (급락 종목 제외)
        if len(closes) >= 6:
            ret5 = (closes[-1] - closes[-6]) / closes[-6] * 100
            conds.append(self._cond(
                '5일 등락률 > -3%', ret5 > -3.0,
                f'{ret5:+.1f}%',
                '등락률(5일) > -3%',
            ))
        else:
            conds.append(self._cond('5일 등락률 > -3%', False, '데이터 부족'))

        # 조건4: 현재가 > SMA(50) — 추가 안전장치
        if len(closes) >= 50:
            sma50 = sum(closes[-50:]) / 50
            conds.append(self._cond(
                '현재가 > SMA(50)', data.close > sma50,
                f'{data.close:,.0f} vs {sma50:,.0f}',
                '현재가 > 이동평균(종가,50)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(50)', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 > 이동평균(종가,200)',
            '이동평균(종가,200) > 이동평균(종가,200)[5일전]',
            '등락률(5일) > -3%',
            '현재가 > 이동평균(종가,50)',
        ]


# ===================================================================
# 4. Larry Hite — Risk-First Trend Following
# ===================================================================

class HiteRiskTrend(WizardStrategy):
    name = 'Hite Risk-First Trend'
    trader = 'Larry Hite'
    category = 'trend_following'
    book = 'MW1989'
    description_text = (
        'Mint Investment. "1 거래에 자산의 1% 이상 리스크 금지." '
        '리스크 관리가 전부. 추세 돌파 + 유동성 필터.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, volumes = data.closes, data.highs, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: 현재가 >= 20일 최고가
        if len(highs) >= 20:
            high20 = max(highs[-20:])
            conds.append(self._cond(
                '현재가 >= 20일 최고가', data.close >= high20,
                f'{data.close:,.0f} vs {high20:,.0f}',
                '현재가 >= MAX(고가, 20)',
            ))
        else:
            conds.append(self._cond('현재가 >= 20일 최고가', False, '데이터 부족'))

        # 조건2: 현재가 > SMA(100)
        if len(closes) >= 100:
            sma100 = sum(closes[-100:]) / 100
            conds.append(self._cond(
                '현재가 > SMA(100)', data.close > sma100,
                f'{data.close:,.0f} vs {sma100:,.0f}',
                '현재가 > 이동평균(종가,100)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(100)', False, '데이터 부족'))

        # 조건3: 거래대금 >= 5억 (유동성)
        turnover = data.daily_turnover
        conds.append(self._cond(
            '거래대금 >= 5억', turnover >= 5.0,
            f'{turnover:,.1f}억',
            '거래대금 >= 5억',
        ))

        # 조건4: ATR 적정 (변동성 너무 높지 않음)
        if len(closes) >= 15 and len(data.highs) >= 15:
            atr_vals = ind.atr(data.highs, data.lows, closes, 14)
            if atr_vals[-1] == atr_vals[-1]:  # not NaN
                atr_pct = atr_vals[-1] / data.close if data.close else 0
                conds.append(self._cond(
                    'ATR(14)/종가 < 5% (적정 변동성)', atr_pct < 0.05,
                    f'{atr_pct:.1%}',
                    'ATR(14)/현재가 < 0.05',
                ))
            else:
                conds.append(self._cond('ATR 적정', False, '계산 불가'))
        else:
            conds.append(self._cond('ATR 적정', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 >= MAX(고가, 20)',
            '현재가 > 이동평균(종가, 100)',
            '거래대금 >= 5억',
            'ATR(14)/현재가 < 0.05',
        ]


# ===================================================================
# 5. Gary Bielfeldt — Concentrated Trend + Pyramiding
# ===================================================================

class BielfeldtConcentratedTrend(WizardStrategy):
    name = 'Bielfeldt Concentrated Trend'
    trader = 'Gary Bielfeldt'
    category = 'trend_following'
    book = 'MW1989'
    description_text = (
        '일리노이 농부. $1,000→수백만 달러. '
        '"잘 아는 시장 하나에 집중." 추세 확인 후 피라미딩.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs = data.closes, data.highs
        conds: list[ConditionResult] = []

        # 조건1: 3선 정배열 SMA(20) > SMA(50) > SMA(200)
        if len(closes) >= 200:
            sma20 = sum(closes[-20:]) / 20
            sma50 = sum(closes[-50:]) / 50
            sma200 = sum(closes[-200:]) / 200
            aligned = sma20 > sma50 > sma200
            conds.append(self._cond(
                'SMA(20) > SMA(50) > SMA(200) 정배열', aligned,
                f'{sma20:,.0f} > {sma50:,.0f} > {sma200:,.0f}',
                '이동평균(종가,20) > 이동평균(종가,50) > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('3선 정배열', False, '데이터 부족'))

        # 조건2: 20일 등락률 > 10% (상승 모멘텀)
        if len(closes) >= 21:
            ret20 = (closes[-1] - closes[-21]) / closes[-21] * 100
            conds.append(self._cond(
                '20일 등락률 > 10%', ret20 > 10.0,
                f'{ret20:+.1f}%',
                '등락률(20일) > 10%',
            ))
        else:
            conds.append(self._cond('20일 등락률 > 10%', False, '데이터 부족'))

        # 조건3: 현재가 > 전일고가 (돌파 확인)
        if len(highs) >= 2:
            conds.append(self._cond(
                '현재가 > 전일고가', data.close > data.prev_high,
                f'{data.close:,.0f} vs {data.prev_high:,.0f}',
                '현재가 > 전일고가',
            ))
        else:
            conds.append(self._cond('현재가 > 전일고가', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '이동평균(종가,20) > 이동평균(종가,50) > 이동평균(종가,200)',
            '등락률(20일) > 10%',
            '현재가 > 전일고가',
        ]


# ===================================================================
# 6. Al Weiss — Ultra-Long-Term Trend
# ===================================================================

class WeissLongTermTrend(WizardStrategy):
    name = 'Weiss Ultra Long-Term Trend'
    trader = 'Al Weiss'
    category = 'trend_following'
    book = 'NMW1992'
    description_text = (
        '21년간 연평균 52%+. 초장기 추세 포착. 월간 차트 기반. '
        '"큰 추세는 몇 년간 지속된다."'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes = data.closes
        conds: list[ConditionResult] = []

        # 조건1: 현재가 > SMA(200)
        if len(closes) >= 200:
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                '현재가 > SMA(200)', data.close > sma200,
                f'{data.close:,.0f} vs {sma200:,.0f}',
                '현재가 > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(200)', False, '데이터 부족'))

        # 조건2: SMA(200) 상승 중 (20일전 대비)
        if len(closes) >= 220:
            sma200_now = sum(closes[-200:]) / 200
            sma200_ago = sum(closes[-220:-20]) / 200
            conds.append(self._cond(
                'SMA(200) 20일간 상승', sma200_now > sma200_ago,
                f'{sma200_now:,.0f} vs 20일전 {sma200_ago:,.0f}',
                '이동평균(종가,200) > 이동평균(종가,200)[20일전]',
            ))
        else:
            conds.append(self._cond('SMA(200) 상승 중', False, '데이터 부족'))

        # 조건3: 반년(120일) 모멘텀 > 30%
        if len(closes) >= 121:
            ret120 = (closes[-1] - closes[-121]) / closes[-121] * 100
            conds.append(self._cond(
                '120일 등락률 > 30%', ret120 > 30.0,
                f'{ret120:+.1f}%',
                '등락률(120일) > 30%',
            ))
        else:
            conds.append(self._cond('120일 등락률 > 30%', False, '데이터 부족'))

        # 조건4: SMA(50) > SMA(200) — 기본 정배열
        if len(closes) >= 200:
            sma50 = sum(closes[-50:]) / 50
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                'SMA(50) > SMA(200)', sma50 > sma200,
                f'{sma50:,.0f} vs {sma200:,.0f}',
                '이동평균(종가,50) > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('SMA(50) > SMA(200)', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 > 이동평균(종가,200)',
            '이동평균(종가,200) > 이동평균(종가,200)[20일전]',
            '등락률(120일) > 30%',
            '이동평균(종가,50) > 이동평균(종가,200)',
        ]


# ===================================================================
# Registry
# ===================================================================

ALL_TREND_FOLLOWERS: list[type[WizardStrategy]] = [
    DennisTurtleSystem1,
    DennisTurtleSystem2,
    SeykotaTrend,
    JonesTrendFilter,
    HiteRiskTrend,
    BielfeldtConcentratedTrend,
    WeissLongTermTrend,
]
