"""Short-term swing trading strategies from Market Wizards.

Traders: Marty Schwartz, Linda Bradford Raschke,
         Victor Sperandeo, Monroe Trout
"""

from __future__ import annotations

from sepa.wizards.base import WizardStrategy, StockData, WizardResult, ConditionResult
from sepa.wizards import indicators as ind


# ===================================================================
# 1. Marty Schwartz — 10 EMA Momentum
# ===================================================================

class SchwartzEma10(WizardStrategy):
    name = 'Schwartz 10-EMA Momentum'
    trader = 'Marty Schwartz'
    category = 'swing'
    book = 'MW1989'
    description_text = (
        '해병대 출신. US Trading Championship 우승. '
        '"나는 펀더멘털로 9년간 잃었고, 기술적 분석으로 부자가 됐다." '
        '10일 EMA 위 = 매수, 아래 = 매도.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes = data.closes
        conds: list[ConditionResult] = []

        # 조건1: 현재가 > EMA(10)
        if len(closes) >= 10:
            ema10 = ind.ema(closes, 10)
            conds.append(self._cond(
                '현재가 > EMA(10)', data.close > ema10[-1],
                f'{data.close:,.0f} vs {ema10[-1]:,.0f}',
                '현재가 > EMA(10)',
            ))

            # 조건2: EMA(10) 상승 중
            conds.append(self._cond(
                'EMA(10) 상승', ema10[-1] > ema10[-2],
                f'{ema10[-1]:,.0f} vs 전일 {ema10[-2]:,.0f}',
                'EMA(10) > EMA(10)[1일전]',
            ))
        else:
            conds.append(self._cond('EMA(10) 위', False, '데이터 부족'))
            conds.append(self._cond('EMA(10) 상승', False, '데이터 부족'))

        # 조건3: RSI(14) 50~70 (과매수 전 진입)
        if len(closes) >= 15:
            rsi_vals = ind.rsi(closes, 14)
            rsi_now = rsi_vals[-1]
            in_zone = 50 < rsi_now < 70 if rsi_now == rsi_now else False
            conds.append(self._cond(
                'RSI(14) 50~70', in_zone,
                f'RSI={rsi_now:.1f}' if rsi_now == rsi_now else 'N/A',
                'RSI(14) > 50 AND RSI(14) < 70',
            ))
        else:
            conds.append(self._cond('RSI 구간', False, '데이터 부족'))

        # 조건4: MACD > Signal
        if len(closes) >= 26:
            macd_line, signal_line, _ = ind.macd(closes)
            conds.append(self._cond(
                'MACD > Signal', macd_line[-1] > signal_line[-1],
                f'MACD={macd_line[-1]:,.0f} vs Sig={signal_line[-1]:,.0f}',
                'MACD > Signal',
            ))
        else:
            conds.append(self._cond('MACD > Signal', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 > EMA(10)',
            'EMA(10) > EMA(10)[1일전]',
            'RSI(14) > 50 AND RSI(14) < 70',
            'MACD > Signal',
        ]


# ===================================================================
# 2. Linda Bradford Raschke — NR7 Breakout + ADX
# ===================================================================

class RaschkeNr7Breakout(WizardStrategy):
    name = 'Raschke NR7 Breakout'
    trader = 'Linda Bradford Raschke'
    category = 'swing'
    book = 'NMW1992'
    description_text = (
        '피트 트레이더 출신. 30년+ 경력. 단기 패턴 전략 개발. '
        'NR7(7일 최소 레인지) 돌파 + ADX 추세 강도 확인.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, lows = data.closes, data.highs, data.lows
        conds: list[ConditionResult] = []

        # 조건1: NR7 — 7일 중 최소 변동폭
        if len(highs) >= 7:
            nr7_flags = ind.nr7(highs, lows)
            # NR7 당일 또는 최근 2일 내
            recent_nr7 = any(nr7_flags[-2:]) if len(nr7_flags) >= 2 else nr7_flags[-1]
            conds.append(self._cond(
                'NR7 (7일 최소 변동폭)', recent_nr7,
                f'최근 NR7={recent_nr7}',
                '(고가-저가) <= MIN(고가-저가, 7)',
            ))
        else:
            conds.append(self._cond('NR7', False, '데이터 부족'))

        # 조건2: ADX(14) > 20
        if len(closes) >= 28:
            adx_vals, _, _ = ind.adx(highs, lows, closes, 14)
            adx_now = adx_vals[-1]
            passed = adx_now > 20 if adx_now == adx_now else False
            conds.append(self._cond(
                'ADX(14) > 20', passed,
                f'ADX={adx_now:.1f}' if adx_now == adx_now else 'N/A',
                'ADX(14) > 20',
            ))
        else:
            conds.append(self._cond('ADX > 20', False, '데이터 부족'))

        # 조건3: 현재가 > SMA(50) — 상승 추세
        if len(closes) >= 50:
            sma50 = sum(closes[-50:]) / 50
            conds.append(self._cond(
                '현재가 > SMA(50)', data.close > sma50,
                f'{data.close:,.0f} vs {sma50:,.0f}',
                '현재가 > 이동평균(종가,50)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(50)', False, '데이터 부족'))

        # 조건4: 현재가 > 전일고가 — 돌파 확인
        if len(highs) >= 2:
            conds.append(self._cond(
                '현재가 > 전일고가 (돌파)', data.close > data.prev_high,
                f'{data.close:,.0f} vs {data.prev_high:,.0f}',
                '현재가 > 전일고가',
            ))
        else:
            conds.append(self._cond('전일고가 돌파', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '(고가-저가) <= MIN(고가-저가, 7)',
            'ADX(14) > 20',
            '현재가 > 이동평균(종가,50)',
            '현재가 > 전일고가',
        ]


# ===================================================================
# 3. Victor Sperandeo — 1-2-3 Trend Reversal
# ===================================================================

class SperandeoTrendReversal(WizardStrategy):
    name = 'Sperandeo 1-2-3 Reversal'
    trader = 'Victor Sperandeo'
    category = 'swing'
    book = 'NMW1992'
    description_text = (
        '18년간 70%+ 승률. 추세선 분석의 대가. '
        '"1-2-3 패턴": 추세선 이탈 → 되돌림 → 직전 고/저점 돌파 = 전환 확인.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, volumes = data.closes, data.highs, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: SMA(20) 상향 돌파 — 단기 추세 전환
        if len(closes) >= 21:
            sma20 = ind.sma(closes, 20)
            # 현재 위, 전일 아래 또는 근접
            above_now = data.close > sma20[-1]
            below_prev = closes[-2] <= sma20[-2] if sma20[-2] == sma20[-2] else False
            conds.append(self._cond(
                'SMA(20) 상향 돌파', above_now and below_prev,
                f'{data.close:,.0f} vs SMA20={sma20[-1]:,.0f}',
                '이동평균(종가,20) 상향 돌파',
            ))

            # 더 느슨한 대안: 그냥 위에 있기만 해도 부분 점수
            if not (above_now and below_prev) and above_now:
                conds[-1] = self._cond(
                    'SMA(20) 상향 돌파/위', above_now,
                    f'{data.close:,.0f} > SMA20={sma20[-1]:,.0f}',
                    '현재가 > 이동평균(종가,20)',
                )
        else:
            conds.append(self._cond('SMA(20) 돌파', False, '데이터 부족'))

        # 조건2: 현재가 > 직전 스윙 고점 ("3번" 확인)
        if len(highs) >= 20:
            # 직전 스윙 고가 = 5~20일 전 구간 최고가
            swing_high = max(highs[-20:-3]) if len(highs) >= 23 else max(highs[-20:-1])
            conds.append(self._cond(
                '현재가 > 직전 스윙 고가', data.close > swing_high,
                f'{data.close:,.0f} vs 스윙고가 {swing_high:,.0f}',
                '현재가 > 직전 스윙 고가',
            ))
        else:
            conds.append(self._cond('스윙 고가 돌파', False, '데이터 부족'))

        # 조건3: 돌파 거래량
        if len(volumes) >= 20:
            vol_avg = sum(volumes[-20:]) / 20
            conds.append(self._cond(
                '거래량 > 20MA × 1.5', data.volume > vol_avg * 1.5,
                f'{data.volume:,.0f} vs {vol_avg * 1.5:,.0f}',
                '거래량 > 이동평균(거래량,20) × 1.5',
            ))
        else:
            conds.append(self._cond('돌파 거래량', False, '데이터 부족'))

        # 조건4: SMA(50) 기울기 전환 (하락→평탄→상승)
        if len(closes) >= 55:
            sma50_vals = ind.sma(closes, 50)
            slope_now = sma50_vals[-1] - sma50_vals[-5] if sma50_vals[-5] == sma50_vals[-5] else 0
            conds.append(self._cond(
                'SMA(50) 기울기 양전환', slope_now > 0,
                f'5일 변화: {slope_now:+,.0f}',
                '이동평균(종가,50) 기울기 평탄→상승',
            ))
        else:
            conds.append(self._cond('SMA(50) 기울기', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '이동평균(종가,20) 상향 돌파',
            '현재가 > 직전 스윙 고가',
            '거래량 > 이동평균(거래량,20) × 1.5',
            '이동평균(종가,50) 기울기 상승 전환',
        ]


# ===================================================================
# 4. Monroe Trout — Statistical Mean Reversion
# ===================================================================

class TroutMeanReversion(WizardStrategy):
    name = 'Trout Statistical Mean Reversion'
    trader = 'Monroe Trout'
    category = 'swing'
    book = 'NMW1992'
    description_text = (
        '하버드 졸업. 연평균 67%, 최대 손실 -8%. '
        '"감정 없는 확률 기반 의사결정." 극단적 과매도 반등 포착.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, lows = data.closes, data.highs, data.lows
        conds: list[ConditionResult] = []

        # 조건1: RSI(5) < 20 — 극단적 과매도 (단기)
        if len(closes) >= 6:
            rsi5 = ind.rsi(closes, 5)
            rsi_now = rsi5[-1]
            passed = rsi_now < 20 if rsi_now == rsi_now else False
            conds.append(self._cond(
                'RSI(5) < 20 (극단 과매도)', passed,
                f'RSI(5)={rsi_now:.1f}' if rsi_now == rsi_now else 'N/A',
                'RSI(5) < 20',
            ))
        else:
            conds.append(self._cond('RSI(5) 과매도', False, '데이터 부족'))

        # 조건2: 현재가 > SMA(200) — 장기 상승 추세 유지
        if len(closes) >= 200:
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                '현재가 > SMA(200) (장기 추세)', data.close > sma200,
                f'{data.close:,.0f} vs {sma200:,.0f}',
                '현재가 > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(200)', False, '데이터 부족'))

        # 조건3: 볼린저밴드 하단 근접
        if len(closes) >= 20:
            upper, middle, lower, bw = ind.bollinger_bands(closes, 20, 2.0)
            if lower[-1] == lower[-1]:
                near_lower = data.close <= lower[-1] * 1.02
                conds.append(self._cond(
                    'BB(20,2) 하단 근접', near_lower,
                    f'{data.close:,.0f} vs BB하단={lower[-1]:,.0f}',
                    '현재가 <= 볼린저밴드(20,2) 하단 × 1.02',
                ))
            else:
                conds.append(self._cond('BB 하단', False, '계산 불가'))
        else:
            conds.append(self._cond('BB 하단', False, '데이터 부족'))

        # 조건4: 3일 등락률 < -5% — 단기 급락
        if len(closes) >= 4:
            ret3 = (closes[-1] - closes[-4]) / closes[-4] * 100
            conds.append(self._cond(
                '3일 등락률 < -5% (급락)', ret3 < -5.0,
                f'{ret3:+.1f}%',
                '등락률(3일) < -5%',
            ))
        else:
            conds.append(self._cond('3일 급락', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            'RSI(5) < 20',
            '현재가 > 이동평균(종가,200)',
            '현재가 <= 볼린저밴드(20,2) 하단 × 1.02',
            '등락률(3일) < -5%',
        ]


# ===================================================================
# Registry
# ===================================================================

ALL_SWING_TRADERS: list[type[WizardStrategy]] = [
    SchwartzEma10,
    RaschkeNr7Breakout,
    SperandeoTrendReversal,
    TroutMeanReversion,
]
