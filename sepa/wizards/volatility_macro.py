"""Volatility contraction and macro-liquidity strategies from Market Wizards.

Traders: Mark Minervini (VCP), Mark Weinstein (Squeeze),
         Stan Druckenmiller (Macro Liquidity), Bill Lipschutz (R:R Filter)
"""

from __future__ import annotations

import math

from sepa.wizards.base import WizardStrategy, StockData, WizardResult, ConditionResult
from sepa.wizards import indicators as ind


# ===================================================================
# 1. Mark Minervini — SEPA Trend Template + VCP
# ===================================================================

class MinerviniTrendTemplate(WizardStrategy):
    name = 'Minervini SEPA Trend Template'
    trader = 'Mark Minervini'
    category = 'volatility_contraction'
    book = 'SMW2001'
    description_text = (
        '고졸 독학. US Investing Championship 155% 우승. 5년 연평균 220%. '
        'SEPA: Trend Template 8조건 + VCP 변동성 수축 패턴 + 실적 가속.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, lows, volumes = data.closes, data.highs, data.lows, data.volumes
        conds: list[ConditionResult] = []

        sma50 = sma150 = sma200 = sma200_prev = 0.0
        has_long = len(closes) >= 222

        if len(closes) >= 200:
            sma50 = sum(closes[-50:]) / 50
            sma150 = sum(closes[-150:]) / 150
            sma200 = sum(closes[-200:]) / 200
        if has_long:
            sma200_prev = sum(closes[-222:-22]) / 200

        # TT1: 현재가 > SMA(150) AND 현재가 > SMA(200)
        if len(closes) >= 200:
            conds.append(self._cond(
                'TT1: 현재가 > SMA(150) & SMA(200)',
                data.close > sma150 and data.close > sma200,
                f'{data.close:,.0f} vs 150MA={sma150:,.0f}, 200MA={sma200:,.0f}',
                '현재가 > 이동평균(종가,150) AND 현재가 > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('TT1', False, '데이터 부족'))

        # TT2: SMA(150) > SMA(200)
        if len(closes) >= 200:
            conds.append(self._cond(
                'TT2: SMA(150) > SMA(200)',
                sma150 > sma200,
                f'{sma150:,.0f} vs {sma200:,.0f}',
                '이동평균(종가,150) > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('TT2', False, '데이터 부족'))

        # TT3: SMA(200) 30일+ 상승 (22 거래일)
        if has_long:
            conds.append(self._cond(
                'TT3: SMA(200) 상승 중',
                sma200 > sma200_prev,
                f'{sma200:,.0f} vs 22일전 {sma200_prev:,.0f}',
                '이동평균(종가,200) > 이동평균(종가,200)[22일전]',
            ))
        else:
            conds.append(self._cond('TT3', False, '데이터 부족'))

        # TT4: SMA(50) > SMA(150) & SMA(200)
        if len(closes) >= 200:
            conds.append(self._cond(
                'TT4: SMA(50) > SMA(150) & SMA(200)',
                sma50 > sma150 and sma50 > sma200,
                f'50MA={sma50:,.0f} vs 150MA={sma150:,.0f}, 200MA={sma200:,.0f}',
                '이동평균(종가,50) > 이동평균(종가,150) AND 이동평균(종가,50) > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('TT4', False, '데이터 부족'))

        # TT5: 현재가 > SMA(50)
        if len(closes) >= 50:
            conds.append(self._cond(
                'TT5: 현재가 > SMA(50)',
                data.close > sma50,
                f'{data.close:,.0f} vs {sma50:,.0f}',
                '현재가 > 이동평균(종가,50)',
            ))
        else:
            conds.append(self._cond('TT5', False, '데이터 부족'))

        # TT6: 현재가 >= 52주 최저가 × 1.25
        if len(lows) >= 252:
            l52 = ind.week52_low(lows)
            conds.append(self._cond(
                'TT6: 52주저가 대비 25%↑',
                data.close >= l52 * 1.25,
                f'{data.close:,.0f} vs {l52 * 1.25:,.0f}',
                '현재가 >= 52주최저가 × 1.25',
            ))
        else:
            conds.append(self._cond('TT6', False, '데이터 부족'))

        # TT7: 현재가 >= 52주 최고가 × 0.75
        if len(highs) >= 252:
            h52 = ind.week52_high(highs)
            conds.append(self._cond(
                'TT7: 52주고가 25% 이내',
                data.close >= h52 * 0.75,
                f'{data.close:,.0f} vs {h52 * 0.75:,.0f}',
                '현재가 >= 52주최고가 × 0.75',
            ))
        else:
            conds.append(self._cond('TT7', False, '데이터 부족'))

        # TT8: RS(120일) >= 70
        rs = ind.relative_strength_percentile(closes, 120)
        conds.append(self._cond(
            'TT8: RS(120) >= 70',
            rs >= 70,
            f'RS={rs:.0f}',
            'RS(120일) >= 70',
        ))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 > 이동평균(종가,150) AND 현재가 > 이동평균(종가,200)',
            '이동평균(종가,150) > 이동평균(종가,200)',
            '이동평균(종가,200) > 이동평균(종가,200)[22일전]',
            '이동평균(종가,50) > 이동평균(종가,150) AND 이동평균(종가,50) > 이동평균(종가,200)',
            '현재가 > 이동평균(종가,50)',
            '현재가 >= 52주최저가 × 1.25',
            '현재가 >= 52주최고가 × 0.75',
            '[계산] RS(120일) >= 70',
        ]


class MinerviniVcp(WizardStrategy):
    name = 'Minervini VCP Pattern'
    trader = 'Mark Minervini'
    category = 'volatility_contraction'
    book = 'SMW2001'
    description_text = (
        'VCP (Volatility Contraction Pattern): 변동성 수축 + 거래량 건조 + 정배열. '
        '돌파 직전의 타이트한 셋업을 포착.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, lows, volumes = data.closes, data.highs, data.lows, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: 3선 정배열
        if len(closes) >= 200:
            sma50 = sum(closes[-50:]) / 50
            sma150 = sum(closes[-150:]) / 150
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                '정배열 SMA(50) > SMA(150) > SMA(200)',
                sma50 > sma150 > sma200,
                f'{sma50:,.0f} > {sma150:,.0f} > {sma200:,.0f}',
                '이동평균(종가,50) > 이동평균(종가,150) > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('정배열', False, '데이터 부족'))

        # 조건2: 현재가 > SMA(50)
        if len(closes) >= 50:
            sma50 = sum(closes[-50:]) / 50
            conds.append(self._cond(
                '현재가 > SMA(50)', data.close > sma50,
                f'{data.close:,.0f} vs {sma50:,.0f}',
                '현재가 > 이동평균(종가,50)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(50)', False, '데이터 부족'))

        # 조건3: 볼린저밴드 폭 < 15% (변동성 수축)
        if len(closes) >= 20:
            _, _, _, bw = ind.bollinger_bands(closes, 20, 2.0)
            bw_now = bw[-1]
            if bw_now == bw_now:
                conds.append(self._cond(
                    'BB폭(20) < 15% (변동성 수축)', bw_now < 15.0,
                    f'{bw_now:.1f}%',
                    '볼린저밴드폭(20) < 15%',
                ))
            else:
                conds.append(self._cond('BB폭', False, '계산 불가'))
        else:
            conds.append(self._cond('BB 변동성', False, '데이터 부족'))

        # 조건4: 거래량 건조 — 최근 5일 < 50일 평균 × 0.6
        if len(volumes) >= 50:
            vol5 = sum(volumes[-5:]) / 5
            vol50 = sum(volumes[-50:]) / 50
            conds.append(self._cond(
                '거래량 건조 (5일avg < 50MA × 0.6)',
                vol5 < vol50 * 0.6,
                f'{vol5:,.0f} vs {vol50 * 0.6:,.0f}',
                '이동평균(거래량,5) < 이동평균(거래량,50) × 0.6',
            ))
        else:
            conds.append(self._cond('거래량 건조', False, '데이터 부족'))

        # 조건5: 52주고가 85% 이상
        if len(highs) >= 252:
            h52 = ind.week52_high(highs)
            conds.append(self._cond(
                '52주고가 85% 이상', data.close >= h52 * 0.85,
                f'{data.close:,.0f} vs {h52 * 0.85:,.0f}',
                '현재가 >= 52주최고가 × 0.85',
            ))
        else:
            conds.append(self._cond('52주고가 근접', False, '데이터 부족'))

        # 조건6: 일봉 변동성 축소 < 2%
        if data.close > 0:
            range_pct = (data.high - data.low) / data.close
            conds.append(self._cond(
                '일봉 레인지 < 2%', range_pct < 0.02,
                f'{range_pct:.1%}',
                '(고가-저가)/종가 < 0.02',
            ))
        else:
            conds.append(self._cond('일봉 레인지', False))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '이동평균(종가,50) > 이동평균(종가,150) > 이동평균(종가,200)',
            '현재가 > 이동평균(종가,50)',
            '볼린저밴드폭(20) < 15%',
            '이동평균(거래량,5) < 이동평균(거래량,50) × 0.6',
            '현재가 >= 52주최고가 × 0.85',
            '(고가-저가)/종가 < 0.02',
        ]


# ===================================================================
# 2. Mark Weinstein — Low Volatility Squeeze
# ===================================================================

class WeinsteinSqueeze(WizardStrategy):
    name = 'Weinstein Low-Vol Squeeze'
    trader = 'Mark Weinstein'
    category = 'volatility_contraction'
    book = 'MW1989'
    description_text = (
        '승률 90%+. "쉬운 거래만 한다." '
        '볼린저밴드 극단 수축 + 조용한 시장 + 상승 추세 내 스퀴즈.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, volumes = data.closes, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: BB폭 < 10% (극단 수축 = 스퀴즈)
        if len(closes) >= 20:
            upper, middle, lower, bw = ind.bollinger_bands(closes, 20, 2.0)
            bw_now = bw[-1]
            if bw_now == bw_now:
                conds.append(self._cond(
                    'BB폭(20) < 10% (스퀴즈)', bw_now < 10.0,
                    f'{bw_now:.1f}%',
                    '볼린저밴드폭(20) < 10%',
                ))
                # 조건4: 현재가 > BB 중심선
                if middle[-1] == middle[-1]:
                    conds.append(self._cond(
                        '현재가 > BB 중심선', data.close > middle[-1],
                        f'{data.close:,.0f} vs {middle[-1]:,.0f}',
                        '현재가 > 볼린저밴드 중심선(20)',
                    ))
                else:
                    conds.append(self._cond('BB 중심선', False))
            else:
                conds.append(self._cond('BB 스퀴즈', False, '계산 불가'))
                conds.append(self._cond('BB 중심선', False, '계산 불가'))
        else:
            conds.append(self._cond('BB 스퀴즈', False, '데이터 부족'))
            conds.append(self._cond('BB 중심선', False, '데이터 부족'))

        # 조건2: 현재가 > SMA(50) — 상승 추세
        if len(closes) >= 50:
            sma50 = sum(closes[-50:]) / 50
            conds.append(self._cond(
                '현재가 > SMA(50)', data.close > sma50,
                f'{data.close:,.0f} vs {sma50:,.0f}',
                '현재가 > 이동평균(종가,50)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(50)', False, '데이터 부족'))

        # 조건3: 거래량 < 20일 평균 × 0.5 (조용한 구간)
        if len(volumes) >= 20:
            vol_avg = sum(volumes[-20:]) / 20
            conds.append(self._cond(
                '거래량 < 20MA × 0.5 (조용)', data.volume < vol_avg * 0.5,
                f'{data.volume:,.0f} vs {vol_avg * 0.5:,.0f}',
                '거래량 < 이동평균(거래량,20) × 0.5',
            ))
        else:
            conds.append(self._cond('조용한 거래량', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '볼린저밴드폭(20) < 10%',
            '현재가 > 이동평균(종가,50)',
            '거래량 < 이동평균(거래량,20) × 0.5',
            '현재가 > 볼린저밴드 중심선(20)',
        ]


# ===================================================================
# 3. Stan Druckenmiller — Macro Liquidity
# ===================================================================

class DruckenmillerMacroLiquidity(WizardStrategy):
    name = 'Druckenmiller Macro Liquidity'
    trader = 'Stan Druckenmiller'
    category = 'macro_liquidity'
    book = 'NMW1992'
    description_text = (
        '소로스 수석 PM. 파운드 공매도 설계자. 30년 무손실. '
        '"확신이 있을 때 크게 배팅." 유동성 방향을 따라라.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, volumes = data.closes, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: 정배열 SMA(50) > SMA(200)
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

        # 조건2: 거래대금 >= 50억 (기관/외인 유동성)
        turnover = data.daily_turnover
        conds.append(self._cond(
            '거래대금 >= 50억', turnover >= 50.0,
            f'{turnover:,.1f}억',
            '거래대금 >= 50억',
        ))

        # 조건3: 외국인 순매수 5일 > 0
        conds.append(self._cond(
            '외국인 5일 순매수 > 0', data.foreign_net_buy_5d > 0,
            f'{data.foreign_net_buy_5d:,.0f}',
            '외국인순매수(5일) > 0',
        ))

        # 조건4: 시장 대비 강세 (20일 등락률 > 0)
        if len(closes) >= 21:
            ret20 = (closes[-1] - closes[-21]) / closes[-21] * 100
            conds.append(self._cond(
                '20일 등락률 > 0 (시장 대비 강세)', ret20 > 0,
                f'{ret20:+.1f}%',
                '등락률(20일) > 0',
            ))
        else:
            conds.append(self._cond('20일 등락률', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '이동평균(종가,50) > 이동평균(종가,200)',
            '거래대금 >= 50억',
            '외국인순매수(5일) > 0',
            '등락률(20일) > 0',
        ]


# ===================================================================
# 4. Bill Lipschutz — R:R Filter (Risk/Reward >= 3:1)
# ===================================================================

class LipschutzRiskReward(WizardStrategy):
    name = 'Lipschutz Risk:Reward Filter'
    trader = 'Bill Lipschutz'
    category = 'macro_liquidity'
    book = 'NMW1992'
    description_text = (
        '살로몬브라더스 FX. 연간 $300M+ 수익. '
        '"R:R 3:1 미만은 절대 안 한다." 비대칭 리스크/리워드.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs = data.closes, data.highs
        conds: list[ConditionResult] = []

        # 목표 상승여력: (52주고가 - 현재가) / 현재가
        if len(highs) >= 252:
            h52 = ind.week52_high(highs)
            upside = (h52 - data.close) / data.close if data.close else 0
            conds.append(self._cond(
                '목표 상승여력 > 15%', upside > 0.15,
                f'{upside:.1%}',
                '(52주최고가 - 현재가) / 현재가 > 0.15',
            ))
        else:
            conds.append(self._cond('상승여력', False, '데이터 부족'))

        # 손절폭: (현재가 - SMA(20)) / 현재가 — 가까울수록 좋음
        if len(closes) >= 20:
            sma20 = sum(closes[-20:]) / 20
            risk = (data.close - sma20) / data.close if data.close else 0
            conds.append(self._cond(
                '손절폭 < 5% (SMA20 근접)', 0 < risk < 0.05,
                f'{risk:.1%}',
                '(현재가 - 이동평균(종가,20)) / 현재가 < 0.05',
            ))
        else:
            conds.append(self._cond('손절폭', False, '데이터 부족'))

        # R:R >= 3:1 계산
        if len(highs) >= 252 and len(closes) >= 20:
            h52 = ind.week52_high(highs)
            sma20 = sum(closes[-20:]) / 20
            reward = h52 - data.close
            risk_amt = data.close - sma20
            if risk_amt > 0:
                rr = reward / risk_amt
                conds.append(self._cond(
                    'R:R >= 3:1', rr >= 3.0,
                    f'R:R = {rr:.1f}:1',
                    'R:R >= 3:1',
                ))
            else:
                conds.append(self._cond('R:R >= 3:1', False, '리스크 음수'))
        else:
            conds.append(self._cond('R:R', False, '데이터 부족'))

        # 현재가 > SMA(50) — 기본 추세
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
            '(52주최고가 - 현재가) / 현재가 > 0.15',
            '(현재가 - 이동평균(종가,20)) / 현재가 < 0.05',
            '[계산] R:R >= 3:1',
            '현재가 > 이동평균(종가,50)',
        ]


# ===================================================================
# 5. Tom Basso — ATR Position Sizing Filter
# ===================================================================

class BassoVolatilityFilter(WizardStrategy):
    name = 'Basso ATR Volatility Filter'
    trader = 'Tom Basso'
    category = 'macro_liquidity'
    book = 'NMW1992'
    description_text = (
        '"Mr. Serenity". "무엇을 사느냐보다 얼마나 사느냐." '
        '변동성 기반 포지션 사이징 필터. ATR 적정 + 추세 확인.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, lows = data.closes, data.highs, data.lows
        conds: list[ConditionResult] = []

        # 조건1: 현재가 > SMA(100)
        if len(closes) >= 100:
            sma100 = sum(closes[-100:]) / 100
            conds.append(self._cond(
                '현재가 > SMA(100)', data.close > sma100,
                f'{data.close:,.0f} vs {sma100:,.0f}',
                '현재가 > 이동평균(종가,100)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(100)', False, '데이터 부족'))

        # 조건2: ATR(14)/현재가 < 3% (적정 변동성)
        if len(closes) >= 15:
            atr_vals = ind.atr(highs, lows, closes, 14)
            atr_pct = atr_vals[-1] / data.close if data.close and atr_vals[-1] == atr_vals[-1] else 0
            conds.append(self._cond(
                'ATR(14)/종가 < 3%', 0 < atr_pct < 0.03,
                f'{atr_pct:.1%}',
                'ATR(14)/현재가 < 0.03',
            ))
        else:
            conds.append(self._cond('ATR 적정', False, '데이터 부족'))

        # 조건3: SMA(50) > SMA(100) — 추세
        if len(closes) >= 100:
            sma50 = sum(closes[-50:]) / 50
            sma100 = sum(closes[-100:]) / 100
            conds.append(self._cond(
                'SMA(50) > SMA(100)', sma50 > sma100,
                f'{sma50:,.0f} vs {sma100:,.0f}',
                '이동평균(종가,50) > 이동평균(종가,100)',
            ))
        else:
            conds.append(self._cond('SMA(50) > SMA(100)', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 > 이동평균(종가,100)',
            'ATR(14)/현재가 < 0.03',
            '이동평균(종가,50) > 이동평균(종가,100)',
        ]


# ===================================================================
# Registry
# ===================================================================

ALL_VOLATILITY_MACRO: list[type[WizardStrategy]] = [
    MinerviniTrendTemplate,
    MinerviniVcp,
    WeinsteinSqueeze,
    DruckenmillerMacroLiquidity,
    LipschutzRiskReward,
    BassoVolatilityFilter,
]
