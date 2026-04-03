"""Growth momentum strategies from Market Wizards.

Traders: William O'Neil, David Ryan, Richard Driehaus,
         Stuart Walton, Steve Cohen
"""

from __future__ import annotations

import math

from sepa.wizards.base import WizardStrategy, StockData, WizardResult, ConditionResult
from sepa.wizards import indicators as ind


# ===================================================================
# 1. William O'Neil — CAN SLIM
# ===================================================================

class ONeilCanSlim(WizardStrategy):
    name = "O'Neil CAN SLIM"
    trader = 'William O\'Neil'
    category = 'growth_momentum'
    book = 'MW1989'
    description_text = (
        "IBD 창립자. CAN SLIM 방법론. "
        "C=EPS QoQ↑25% / A=EPS YoY↑25% / N=신고가·신제품 / "
        "S=유통주식·수급 / L=업종선도 / I=기관매수 / M=시장방향."
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, volumes = data.closes, data.highs, data.volumes
        conds: list[ConditionResult] = []

        # N — 52주 고가 근접 (75% 이상)
        if len(highs) >= 252:
            h52 = ind.week52_high(highs)
            near = data.close >= h52 * 0.75
            conds.append(self._cond(
                '52주 고가 × 0.75 이상 (N)', near,
                f'{data.close:,.0f} vs {h52 * 0.75:,.0f}',
                '현재가 >= 52주최고가 × 0.75',
            ))
        else:
            conds.append(self._cond('52주고가 근접 (N)', False, '데이터 부족'))

        # 현재가 > SMA(50)
        if len(closes) >= 50:
            sma50 = sum(closes[-50:]) / 50
            conds.append(self._cond(
                '현재가 > SMA(50)', data.close > sma50,
                f'{data.close:,.0f} vs {sma50:,.0f}',
                '현재가 > 이동평균(종가,50)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(50)', False, '데이터 부족'))

        # SMA(50) > SMA(200) — 정배열
        if len(closes) >= 200:
            sma50 = sum(closes[-50:]) / 50
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                'SMA(50) > SMA(200) 정배열', sma50 > sma200,
                f'{sma50:,.0f} vs {sma200:,.0f}',
                '이동평균(종가,50) > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('SMA(50) > SMA(200)', False, '데이터 부족'))

        # S — 거래량 > 50일 평균 × 1.5 (수급)
        if len(volumes) >= 50:
            vol_avg = sum(volumes[-50:]) / 50
            conds.append(self._cond(
                '거래량 > 50일 평균 × 1.5 (S)', data.volume > vol_avg * 1.5,
                f'{data.volume:,.0f} vs {vol_avg * 1.5:,.0f}',
                '거래량 > 이동평균(거래량,50) × 1.5',
            ))
        else:
            conds.append(self._cond('거래량 수급 (S)', False, '데이터 부족'))

        # 양봉 — 등락률 > 0
        conds.append(self._cond(
            '당일 양봉', data.daily_change_pct > 0,
            f'{data.daily_change_pct:+.1f}%',
            '등락률(1일) > 0',
        ))

        # I — 시가총액 >= 1000억 (기관 관심)
        if not self._safe_nan(data.market_cap):
            conds.append(self._cond(
                '시가총액 >= 1000억 (I)', data.market_cap >= 1000,
                f'{data.market_cap:,.0f}억',
                '시가총액 >= 1000억',
            ))
        else:
            conds.append(self._cond('시가총액 (I)', True, '데이터 미제공 — 통과'))

        # C — EPS QoQ >= 25%
        if not self._safe_nan(data.eps_qoq):
            conds.append(self._cond(
                'EPS QoQ >= 25% (C)', data.eps_qoq >= 25,
                f'{data.eps_qoq:+.1f}%',
                'EPS QoQ >= 25%',
            ))
        else:
            conds.append(self._cond('EPS QoQ (C)', True, '데이터 미제공 — 통과'))

        # A — EPS YoY >= 25%
        if not self._safe_nan(data.eps_yoy):
            conds.append(self._cond(
                'EPS YoY >= 25% (A)', data.eps_yoy >= 25,
                f'{data.eps_yoy:+.1f}%',
                'EPS YoY >= 25%',
            ))
        else:
            conds.append(self._cond('EPS YoY (A)', True, '데이터 미제공 — 통과'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 >= 52주최고가 × 0.75',
            '현재가 > 이동평균(종가,50)',
            '이동평균(종가,50) > 이동평균(종가,200)',
            '거래량 > 이동평균(거래량,50) × 1.5',
            '등락률(1일) > 0',
            '시가총액 >= 1000억',
            '[수동] EPS QoQ >= 25%',
            '[수동] EPS YoY >= 25%',
        ]


# ===================================================================
# 2. David Ryan — O'Neil + VCP Specialist
# ===================================================================

class RyanVcpGrowth(WizardStrategy):
    name = 'Ryan VCP Growth'
    trader = 'David Ryan'
    category = 'growth_momentum'
    book = 'MW1989'
    description_text = (
        "O'Neil 제자. US Investing Championship 3연패. "
        "EPS 가속 + 컵앤핸들/VCP 패턴 전문. 7~8% 손절."
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, lows, volumes = data.closes, data.highs, data.lows, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: 52주 고가 × 0.85 이상
        if len(highs) >= 252:
            h52 = ind.week52_high(highs)
            conds.append(self._cond(
                '52주고가 85% 이상', data.close >= h52 * 0.85,
                f'{data.close:,.0f} vs {h52 * 0.85:,.0f}',
                '현재가 >= 52주최고가 × 0.85',
            ))
        else:
            conds.append(self._cond('52주고가 85%', False, '데이터 부족'))

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

        # 조건3: 변동성 수축 — 일봉 범위 < 3%
        if data.close > 0:
            range_pct = (data.high - data.low) / data.close
            conds.append(self._cond(
                '일봉 변동성 < 3% (VCP)', range_pct < 0.03,
                f'{range_pct:.1%}',
                '(고가-저가)/종가 < 0.03',
            ))
        else:
            conds.append(self._cond('변동성 수축', False))

        # 조건4: 거래량 < 50일 평균 × 0.7 (건조)
        if len(volumes) >= 50:
            vol_avg = sum(volumes[-50:]) / 50
            dryup = data.volume < vol_avg * 0.7
            conds.append(self._cond(
                '거래량 건조 < 50MA × 0.7', dryup,
                f'{data.volume:,.0f} vs {vol_avg * 0.7:,.0f}',
                '거래량 < 이동평균(거래량,50) × 0.7',
            ))
        else:
            conds.append(self._cond('거래량 건조', False, '데이터 부족'))

        # 조건5: 3선 정배열
        if len(closes) >= 200:
            sma50 = sum(closes[-50:]) / 50
            sma150 = sum(closes[-150:]) / 150
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                'SMA(50) > SMA(150) > SMA(200)', sma50 > sma150 > sma200,
                f'{sma50:,.0f} > {sma150:,.0f} > {sma200:,.0f}',
                '이동평균(종가,50) > 이동평균(종가,150) > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('3선 정배열', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 >= 52주최고가 × 0.85',
            '현재가 > 이동평균(종가,50)',
            '(고가-저가)/종가 < 0.03',
            '거래량 < 이동평균(거래량,50) × 0.7',
            '이동평균(종가,50) > 이동평균(종가,150) > 이동평균(종가,200)',
        ]


# ===================================================================
# 3. Richard Driehaus — Momentum + Earnings Surprise
# ===================================================================

class DriehausMomentum(WizardStrategy):
    name = 'Driehaus Growth Momentum'
    trader = 'Richard Driehaus'
    category = 'growth_momentum'
    book = 'NMW1992'
    description_text = (
        '모멘텀 투자의 아버지. "높게 사서 더 높게 판다." '
        'EPS 서프라이즈 + 가격 모멘텀. 소형 성장주 집중.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, volumes = data.closes, data.highs, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: 60일 등락률 > 20%
        if len(closes) >= 61:
            ret60 = (closes[-1] - closes[-61]) / closes[-61] * 100
            conds.append(self._cond(
                '60일 모멘텀 > 20%', ret60 > 20.0,
                f'{ret60:+.1f}%',
                '등락률(60일) > 20%',
            ))
        else:
            conds.append(self._cond('60일 모멘텀', False, '데이터 부족'))

        # 조건2: 52주고가 90% 이상
        if len(highs) >= 252:
            h52 = ind.week52_high(highs)
            conds.append(self._cond(
                '52주고가 90% 이상', data.close >= h52 * 0.90,
                f'{data.close:,.0f} vs {h52 * 0.90:,.0f}',
                '현재가 >= 52주최고가 × 0.90',
            ))
        else:
            conds.append(self._cond('52주고가 근접', False, '데이터 부족'))

        # 조건3: 3선 정배열 SMA(20) > SMA(50) > SMA(200)
        if len(closes) >= 200:
            sma20 = sum(closes[-20:]) / 20
            sma50 = sum(closes[-50:]) / 50
            sma200 = sum(closes[-200:]) / 200
            conds.append(self._cond(
                'SMA(20) > SMA(50) > SMA(200)', sma20 > sma50 > sma200,
                f'{sma20:,.0f} > {sma50:,.0f} > {sma200:,.0f}',
                '이동평균(종가,20) > 이동평균(종가,50) > 이동평균(종가,200)',
            ))
        else:
            conds.append(self._cond('3선 정배열', False, '데이터 부족'))

        # 조건4: 거래량 > 20일 평균
        if len(volumes) >= 20:
            vol_avg = sum(volumes[-20:]) / 20
            conds.append(self._cond(
                '거래량 > 20일 평균', data.volume > vol_avg,
                f'{data.volume:,.0f} vs {vol_avg:,.0f}',
                '거래량 > 이동평균(거래량,20)',
            ))
        else:
            conds.append(self._cond('거래량 확인', False, '데이터 부족'))

        # 조건5: 시가총액 < 1조 (소형/중형)
        if not self._safe_nan(data.market_cap):
            conds.append(self._cond(
                '시가총액 < 1조 (소형/중형)', data.market_cap < 10000,
                f'{data.market_cap:,.0f}억',
                '시가총액 < 10000억',
            ))
        else:
            conds.append(self._cond('시가총액', True, '데이터 미제공 — 통과'))

        # 조건6: EPS 가속 (펀더멘털)
        if not self._safe_nan(data.eps_qoq):
            conds.append(self._cond(
                'EPS QoQ 양수 (실적 가속)', data.eps_qoq > 0,
                f'{data.eps_qoq:+.1f}%',
                'EPS QoQ > 0%',
            ))
        else:
            conds.append(self._cond('EPS 가속', True, '데이터 미제공 — 통과'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '등락률(60일) > 20%',
            '현재가 >= 52주최고가 × 0.90',
            '이동평균(종가,20) > 이동평균(종가,50) > 이동평균(종가,200)',
            '거래량 > 이동평균(거래량,20)',
            '시가총액 < 10000억',
            '[수동] EPS QoQ 가속 확인',
        ]


# ===================================================================
# 4. Stuart Walton — Stage 2 Entry
# ===================================================================

class WaltonStage2Entry(WizardStrategy):
    name = 'Walton Stage 2 Entry'
    trader = 'Stuart Walton'
    category = 'growth_momentum'
    book = 'SMW2001'
    description_text = (
        '성장주 전문. "최고의 종목은 초기 움직임에서 알아볼 수 있다." '
        'Stage 1→2 전환 포착. 골든크로스 + 강한 돌파.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, highs, volumes = data.closes, data.highs, data.volumes
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

        # 조건2: 골든크로스 근접 — SMA(50) / SMA(200) 비율 근접
        if len(closes) >= 200:
            sma50 = sum(closes[-50:]) / 50
            sma200 = sum(closes[-200:]) / 200
            ratio = sma50 / sma200 if sma200 else 0
            # 골든크로스 직후 (비율 1.0~1.05)
            near_gc = 0.98 <= ratio <= 1.10
            conds.append(self._cond(
                'SMA(50)/SMA(200) 골든크로스 구간', near_gc,
                f'비율 {ratio:.3f}',
                '이동평균(종가,50) ≈ 이동평균(종가,200) (골든크로스)',
            ))
        else:
            conds.append(self._cond('골든크로스', False, '데이터 부족'))

        # 조건3: 거래량 > 50일 평균 × 2.0 (매집)
        if len(volumes) >= 50:
            vol_avg = sum(volumes[-50:]) / 50
            conds.append(self._cond(
                '거래량 > 50MA × 2.0 (매집)', data.volume > vol_avg * 2.0,
                f'{data.volume:,.0f} vs {vol_avg * 2.0:,.0f}',
                '거래량 > 이동평균(거래량,50) × 2.0',
            ))
        else:
            conds.append(self._cond('매집 거래량', False, '데이터 부족'))

        # 조건4: 3일 등락률 > 5% (힘 있는 돌파)
        if len(closes) >= 4:
            ret3 = (closes[-1] - closes[-4]) / closes[-4] * 100
            conds.append(self._cond(
                '3일 등락률 > 5%', ret3 > 5.0,
                f'{ret3:+.1f}%',
                '등락률(3일) > 5%',
            ))
        else:
            conds.append(self._cond('3일 등락률', False, '데이터 부족'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '현재가 > 이동평균(종가,200)',
            '이동평균(종가,50) ≈ 이동평균(종가,200) (골든크로스 구간)',
            '거래량 > 이동평균(거래량,50) × 2.0',
            '등락률(3일) > 5%',
        ]


# ===================================================================
# 5. Steve Cohen — Event-Driven Momentum
# ===================================================================

class CohenEventMomentum(WizardStrategy):
    name = 'Cohen Event-Driven Momentum'
    trader = 'Steve Cohen'
    category = 'growth_momentum'
    book = 'SMW2001'
    description_text = (
        'SAC Capital. 14년 연평균 40%+. '
        '"주가 40%=시장, 30%=섹터, 30%=종목." '
        '촉매 이벤트 + 섹터 순풍 + 폭발적 거래량.'
    )

    def screen(self, data: StockData) -> WizardResult:
        closes, volumes = data.closes, data.volumes
        conds: list[ConditionResult] = []

        # 조건1: 당일 등락률 > 3% (촉매 반응)
        conds.append(self._cond(
            '당일 등락률 > 3% (촉매)', data.daily_change_pct > 3.0,
            f'{data.daily_change_pct:+.1f}%',
            '등락률(1일) > 3%',
        ))

        # 조건2: 거래량 > 20일 평균 × 3.0 (이벤트 폭발)
        if len(volumes) >= 20:
            vol_avg = sum(volumes[-20:]) / 20
            conds.append(self._cond(
                '거래량 > 20MA × 3.0 (이벤트)', data.volume > vol_avg * 3.0,
                f'{data.volume:,.0f} vs {vol_avg * 3.0:,.0f}',
                '거래량 > 이동평균(거래량,20) × 3.0',
            ))
        else:
            conds.append(self._cond('이벤트 거래량', False, '데이터 부족'))

        # 조건3: 현재가 > SMA(50)
        if len(closes) >= 50:
            sma50 = sum(closes[-50:]) / 50
            conds.append(self._cond(
                '현재가 > SMA(50)', data.close > sma50,
                f'{data.close:,.0f} vs {sma50:,.0f}',
                '현재가 > 이동평균(종가,50)',
            ))
        else:
            conds.append(self._cond('현재가 > SMA(50)', False, '데이터 부족'))

        # 조건4: 섹터 5일 등락률 > 0 (순풍)
        if not self._safe_nan(data.sector_index_change_5d):
            conds.append(self._cond(
                '섹터 5일 등락률 > 0 (순풍)', data.sector_index_change_5d > 0,
                f'{data.sector_index_change_5d:+.1f}%',
                '업종지수 등락률(5일) > 0',
            ))
        else:
            conds.append(self._cond('섹터 순풍', True, '데이터 미제공 — 통과'))

        return self._result(data.symbol, conds)

    def kiwoom_conditions(self) -> list[str]:
        return [
            '등락률(1일) > 3%',
            '거래량 > 이동평균(거래량,20) × 3.0',
            '현재가 > 이동평균(종가,50)',
            '업종지수 등락률(5일) > 0',
        ]


# ===================================================================
# Registry
# ===================================================================

ALL_GROWTH_MOMENTUM: list[type[WizardStrategy]] = [
    ONeilCanSlim,
    RyanVcpGrowth,
    DriehausMomentum,
    WaltonStage2Entry,
    CohenEventMomentum,
]
