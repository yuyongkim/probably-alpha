"""Contrarian and value strategies from Market Wizards.

Traders: James B. Rogers Jr., Michael Steinhardt,
         Ahmet Okumus, Dana Galante (short-seller)
"""

from __future__ import annotations

from sepa.wizards.base import WizardStrategy, StockData, WizardResult, ConditionResult
from sepa.wizards import indicators as ind


# ===================================================================
# 1. James B. Rogers Jr. — Deep Contrarian Value
# ===================================================================

class RogersDeepValue(WizardStrategy):
    name = 'Rogers Deep Contrarian'
    trader = 'James B. Rogers Jr.'
    category = 'contrarian_value'
    book = 'MW1989'
    description_text = (
        '소로스와 Quantum Fund 공동 설립. 10년 4,200%. '
        '"남들이 보지 않는 곳에서 변화를 찾아라." '
        '극단적 소외 + 저평가 + 실적 바닥 확인.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, lows, volumes = data.closes, data.lows, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: PER < 업종평균 × 0.5
        if not self._safe_nan(data.per) and not self._safe_nan(data.sector_avg_per):
            threshold = data.sector_avg_per * 0.5
            conds.append(self._cond(
                'PER < 업종평균 × 0.5', data.per < threshold and data.per > 0,
                f'PER={data.per:.1f} vs 기준={threshold:.1f}',
                'PER < 업종평균PER × 0.5',
            ))
        else:
            conds.append(self._cond('PER 저평가', True, '데이터 미제공 — 통과'))

        # 조건2: PBR < 1.0
        if not self._safe_nan(data.pbr):
            conds.append(self._cond(
                'PBR < 1.0', data.pbr < 1.0 and data.pbr > 0,
                f'PBR={data.pbr:.2f}',
                'PBR < 1.0',
            ))
        else:
            conds.append(self._cond('PBR < 1.0', True, '데이터 미제공 — 통과'))

        # 조건3: 거래량 < 60일 평균 × 0.3 (극단적 무관심)
        if len(volumes) >= 60:
            vol_avg = sum(volumes[-60:]) / 60
            conds.append(self._cond(
                '거래량 < 60MA × 0.3 (무관심)', data.volume < vol_avg * 0.3,
                f'{data.volume:,.0f} vs {vol_avg * 0.3:,.0f}',
                '거래량 < 이동평균(거래량,60) × 0.3',
            ))
        else:
            conds.append(self._cond('극단적 무관심', False, '데이터 부족'))

        # 조건4: 52주 최저가 근접 (현재가 < 52주최저 × 1.15)
        if len(lows) >= 252:
            l52 = ind.week52_low(lows)
            conds.append(self._cond(
                '52주최저 근접', data.close < l52 * 1.15,
                f'{data.close:,.0f} vs {l52 * 1.15:,.0f}',
                '현재가 < 52주최저가 × 1.15',
            ))
        else:
            conds.append(self._cond('52주최저 근접', False, '데이터 부족'))

        # 조건5: 매출성장률 > 0 (실적 바닥 확인)
        if not self._safe_nan(data.revenue_growth):
            conds.append(self._cond(
                '매출성장률 > 0 (바닥 확인)', data.revenue_growth > 0,
                f'{data.revenue_growth:+.1f}%',
                '매출성장률 > 0',
            ))
        else:
            conds.append(self._cond('매출성장률', True, '데이터 미제공 — 통과'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            'PER < 업종평균PER × 0.5',
            'PBR < 1.0',
            '거래량 < 이동평균(거래량,60) × 0.3',
            '현재가 < 52주최저가 × 1.15',
            '[수동] 매출성장률 > 0',
        ]


# ===================================================================
# 2. Michael Steinhardt — Variant Perception (Oversold Bounce)
# ===================================================================

class SteinhardtVariantPerception(WizardStrategy):
    name = 'Steinhardt Variant Perception'
    trader = 'Michael Steinhardt'
    category = 'contrarian_value'
    book = 'MW1989'
    description_text = (
        '21년 연평균 24.5%. "변형 인식" — 시장 컨센서스와 다른 견해. '
        '장기 추세 살아있는 상태에서 과매도 반등 포착.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, volumes = data.closes, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: RSI(14) < 30 — 과매도
        if len(closes) >= 15:
            rsi_vals = ind.rsi(closes, 14)
            rsi_now = rsi_vals[-1]
            passed = rsi_now < 30 if rsi_now == rsi_now else False
            conds.append(self._cond(
                'RSI(14) < 30 (과매도)', passed,
                f'RSI={rsi_now:.1f}' if rsi_now == rsi_now else 'N/A',
                'RSI(14) < 30',
            ))
        else:
            conds.append(self._cond('RSI 과매도', False, '데이터 부족'))

        # 조건2: 현재가 > SMA(200) — 장기 추세 생존
        if len(closes) >= 200:
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                '현재가 > SMA(200) (장기 추세 유지)', data.close > sma200,
                f'{data.close:,.0f} vs {sma200:,.0f}',
                '현재가 > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(200)', False, '데이터 부족'))

        # 조건3: 거래량 > 20일 평균 × 2.0 — 반등 수급 유입
        if len(volumes) >= 20:
            vol_avg = sum(volumes[-20:]) / 20
            conds.append(self._cond(
                '거래량 > 20MA × 2.0 (반등 수급)', data.volume > vol_avg * 2.0,
                f'{data.volume:,.0f} vs {vol_avg * 2.0:,.0f}',
                '거래량 > 이동평균(거래량,20) × 2.0',
            ))
        else:
            conds.append(self._cond('반등 거래량', False, '데이터 부족'))

        # 조건4: 당일 등락률 > 2% — 반등 시작
        conds.append(self._cond(
            '당일 등락률 > 2% (반등)', data.daily_change_pct > 2.0,
            f'{data.daily_change_pct:+.1f}%',
            '등락률(1일) > 2%',
        ))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            'RSI(14) < 30',
            '현재가 > 이동평균(종가,200)',
            '거래량 > 이동평균(거래량,20) × 2.0',
            '등락률(1일) > 2%',
        ]


# ===================================================================
# 3. Ahmet Okumus — Deep Value + Turnaround Catalyst
# ===================================================================

class OkumusDeepValueTurnaround(WizardStrategy):
    name = 'Okumus Deep Value Turnaround'
    trader = 'Ahmet Okumus'
    category = 'contrarian_value'
    book = 'SMW2001'
    description_text = (
        '터키 출신. 연평균 40%+. '
        '"50센트짜리 1달러를 사라 — 단, 1달러로 가게 할 촉매가 있어야." '
        '극단적 저PBR/PER + 낮은 부채 + 턴어라운드.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, lows, volumes = data.closes, data.highs, data.lows, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: PBR < 0.7
        if not self._safe_nan(data.pbr):
            conds.append(self._cond(
                'PBR < 0.7', data.pbr < 0.7 and data.pbr > 0,
                f'PBR={data.pbr:.2f}',
                'PBR < 0.7',
            ))
        else:
            conds.append(self._cond('PBR < 0.7', True, '데이터 미제공 — 통과'))

        # 조건2: PER < 8
        if not self._safe_nan(data.per):
            conds.append(self._cond(
                'PER < 8', data.per < 8 and data.per > 0,
                f'PER={data.per:.1f}',
                'PER < 8',
            ))
        else:
            conds.append(self._cond('PER < 8', True, '데이터 미제공 — 통과'))

        # 조건3: 부채비율 < 100%
        if not self._safe_nan(data.debt_ratio):
            conds.append(self._cond(
                '부채비율 < 100%', data.debt_ratio < 100,
                f'{data.debt_ratio:.0f}%',
                '부채비율 < 100%',
            ))
        else:
            conds.append(self._cond('부채비율', True, '데이터 미제공 — 통과'))

        # 조건4: 고점 대비 50% 이상 하락
        if len(highs) >= 252:
            h52 = ind.week52_high(highs)
            conds.append(self._cond(
                '52주고가 대비 50%+ 하락', data.close < h52 * 0.50,
                f'{data.close:,.0f} vs {h52 * 0.50:,.0f}',
                '현재가 < 52주최고가 × 0.50',
            ))
        else:
            conds.append(self._cond('고점 대비 하락', False, '데이터 부족'))

        # 조건5: 5일 등락률 > 0 (바닥 반등 시작)
        if len(closes) >= 6:
            ret5 = (closes[-1] - closes[-6]) / closes[-6] * 100
            conds.append(self._cond(
                '5일 등락률 > 0 (반등 시작)', ret5 > 0,
                f'{ret5:+.1f}%',
                '등락률(5일) > 0',
            ))
        else:
            conds.append(self._cond('5일 반등', False, '데이터 부족'))

        # 조건6: 거래량 > 20일 평균 × 1.5 (수급 유입)
        if len(volumes) >= 20:
            vol_avg = sum(volumes[-20:]) / 20
            conds.append(self._cond(
                '거래량 > 20MA × 1.5 (수급)', data.volume > vol_avg * 1.5,
                f'{data.volume:,.0f} vs {vol_avg * 1.5:,.0f}',
                '거래량 > 이동평균(거래량,20) × 1.5',
            ))
        else:
            conds.append(self._cond('수급 유입', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            'PBR < 0.7',
            'PER < 8',
            '부채비율 < 100%',
            '현재가 < 52주최고가 × 0.50',
            '등락률(5일) > 0',
            '거래량 > 이동평균(거래량,20) × 1.5',
        ]


# ===================================================================
# 4. Dana Galante — Short-Selling Setup
# ===================================================================

class GalanteShortSetup(WizardStrategy):
    name = 'Galante Short-Sell Setup'
    trader = 'Dana Galante'
    category = 'contrarian_value'
    book = 'SMW2001'
    description_text = (
        '공매도 전문. 2000년 IT 버블 붕괴 시 큰 수익. '
        '"성장이 멈추는 순간을 잡아라." 과대평가 + 데드크로스 + 매도세 유입.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, volumes = data.closes, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: PER > 업종평균 × 2.0 (과대평가)
        if not self._safe_nan(data.per) and not self._safe_nan(data.sector_avg_per):
            threshold = data.sector_avg_per * 2.0
            conds.append(self._cond(
                'PER > 업종평균 × 2.0 (과대평가)', data.per > threshold,
                f'PER={data.per:.1f} vs 기준={threshold:.1f}',
                'PER > 업종평균PER × 2.0',
            ))
        else:
            conds.append(self._cond('PER 과대평가', True, '데이터 미제공 — 통과'))

        # 조건2: 현재가 < SMA(50)
        if len(closes) >= 50:
            sma50 = sum(closes[-50:]) / 50
            conds.append(self._cond(
                '현재가 < SMA(50)', data.close < sma50,
                f'{data.close:,.0f} vs {sma50:,.0f}',
                '현재가 < 이동평균(종가,50)',
            ))
        else:
            conds.append(self._cond('현재가 < SMA(50)', False, '데이터 부족'))

        # 조건3: 데드크로스 SMA(50) < SMA(200)
        if len(closes) >= 200:
            sma50 = sum(closes[-50:]) / 50
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                'SMA(50) < SMA(200) 데드크로스', sma50 < sma200,
                f'{sma50:,.0f} vs {sma200:,.0f}',
                '이동평균(종가,50) < 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('데드크로스', False, '데이터 부족'))

        # 조건4: 거래량 > 20일 평균 × 1.5 (매도세 유입)
        if len(volumes) >= 20:
            vol_avg = sum(volumes[-20:]) / 20
            conds.append(self._cond(
                '거래량 > 20MA × 1.5 (매도세)', data.volume > vol_avg * 1.5,
                f'{data.volume:,.0f} vs {vol_avg * 1.5:,.0f}',
                '거래량 > 이동평균(거래량,20) × 1.5',
            ))
        else:
            conds.append(self._cond('매도세 거래량', False, '데이터 부족'))

        # 조건5: 20일 등락률 < -10% (하락 모멘텀)
        if len(closes) >= 21:
            ret20 = (closes[-1] - closes[-21]) / closes[-21] * 100
            conds.append(self._cond(
                '20일 등락률 < -10% (하락 모멘텀)', ret20 < -10.0,
                f'{ret20:+.1f}%',
                '등락률(20일) < -10%',
            ))
        else:
            conds.append(self._cond('20일 하락', False, '데이터 부족'))

        return self._result(data.symbol, conds, metadata={'direction': 'short'})

    def kiwoom_conditions(self) -> list[str]:
        return [
            'PER > 업종평균PER × 2.0',
            '현재가 < 이동평균(종가,50)',
            '이동평균(종가,50) < 이동평균(종가,200)',
            '거래량 > 이동평균(거래량,20) × 1.5',
            '등락률(20일) < -10%',
        ]


# ===================================================================
# Registry
# ===================================================================

ALL_CONTRARIAN_VALUE: list[type[WizardStrategy]] = [
    RogersDeepValue,
    SteinhardtVariantPerception,
    OkumusDeepValueTurnaround,
    GalanteShortSetup,
]
