# STRATEGY_FAMILIES.md
> 전략군 분류 및 SEPA 시스템 반영 위치 정의.
> 원전 조건식: MARKET_WIZARDS_KIWOOM_CONDITIONS_KO.md

---

## Family A: 추세추종 (Trend Following)

핵심: MA 정배열, 신고가 돌파, ATR 사이징, 추세 이탈 시 청산
대표: Dennis, Seykota, Hite, Bielfeldt, Jones

키움 마스터 조건식:
```
조건1: MA50 > MA150 > MA200
조건2: 현재가 > MA50
조건3: MA200 > MA200[22일전]
조건4: 현재가 >= MAX(고가, 20)
조건5: 거래량 > 이동평균(거래량,20)
```

SEPA 반영:
- Alpha: Trend Template 8조건 중 정배열/200MA 기울기
- Delta: ATR/변동성 기반 사이징

---

## Family B: 성장주 모멘텀 (Growth Momentum)

핵심: 52주 고가 근접, RS 상위, EPS 가속 >=25%, VCP 진입
대표: O'Neil, Ryan, Driehaus, Minervini, Cohen, Walton

키움 마스터 조건식:
```
조건1: 현재가 > MA150 AND 현재가 > MA200
조건2: MA50 > MA150
조건3: 현재가 >= 52주최저가 * 1.25
조건4: 현재가 >= 52주최고가 * 0.75
조건5: 거래량 > 이동평균(거래량,50) * 1.5

[펀더멘털]
EPS QoQ >= 25%, EPS YoY >= 25%, ROE >= 15%
```

SEPA 반영:
- Alpha: Trend Template 8조건 전체
- Beta: VCP 패턴
- Gamma: EPS/매출 가속

---

## Family C: 단기 스윙 (Short-term Swing)

핵심: EMA10, RSI 40~65, ADX>20, NR7/좁은 레인지
대표: Schwartz, Raschke, Trout

조건식 예:
```
조건1: 현재가 > EMA(10)
조건2: RSI(14) > 40 AND RSI(14) < 65
조건3: ADX(14) > 20
조건4: (고가-저가)/종가 < 0.025
조건5: 현재가 > MA50
```

SEPA 반영:
- Beta: NR7/좁은 레인지 보완
- 향후 별도 Swing Agent

---

## Family D: 역발상/가치 (Contrarian / Value)

핵심: PBR<0.8, PER 업종대비 40% 할인, 52주 고점대비 45%+ 하락, RSI<35, 반등 촉매
대표: Rogers, Steinhardt, Okumus

조건식 예:
```
조건1: PBR < 0.8
조건2: PER < 업종평균PER * 0.6
조건3: 부채비율 < 120%
조건4: 현재가 < 52주최고가 * 0.55
조건5: RSI(14) < 35
조건6: 거래량 > 이동평균(거래량,20) * 1.3
```

SEPA 반영:
- 현재 미구현 → Value Agent (향후)

---

## Family E: VCP / 변동성 수축 돌파

핵심: 추세 정배열, 볼린저밴드 수축, 거래량 건조, 고가 85%+ 근접
대표: Minervini(VCP), Ryan(컵앤핸들), Weinstein(스퀴즈)

조건식 예:
```
조건1: MA50 > MA150 > MA200
조건2: 현재가 > MA50
조건3: 볼린저밴드폭(20) < 15%
조건4: 거래량 < 이동평균(거래량,50) * 0.6
조건5: 현재가 >= 52주최고가 * 0.85
조건6: (고가-저가)/종가 < 0.02
```

SEPA 반영:
- Beta 핵심 에이전트

---

## Family F: 글로벌 매크로

핵심: 중앙은행/금리/환율, 유동성 방향, 외인 수급
대표: Kovner, Druckenmiller, Weiss

SEPA 반영:
- Gamma: 화학 업황(유가/PMI/CAPEX), FRED/ECOS 연동
- 향후 Macro Agent로 확장

---

## Family G: 공매도

핵심: 과대평가, 실적 둔화, 차트 붕괴
대표: Galante

SEPA 반영:
- 현재 미구현 → Short Agent (향후)

---

## 에이전트 ↔ 전략군 매핑 요약

| Agent | 주요 전략군 | 보완 |
|-------|-----------|------|
| Alpha | B (성장 모멘텀) | A (추세추종) |
| Beta  | E (VCP) | C (스윙/NR7) |
| Gamma | B (실적 가속) | F (매크로) |
| Delta | A (ATR) | B (7~8% 손절) |
| Omega | B+E 종합 | 전체 통합 |
| Leader Sector | A+B breadth | F (매크로 체크) |
| Leader Stock  | B (RS+TT+VCP) | E (수축 준비) |

---

## 미구현 / 향후 확장

| Family | 에이전트 | 우선순위 |
|--------|---------|---------|
| D (역발상/가치) | Value Agent | 중 |
| G (공매도)      | Short Agent | 낮 |
| C (단기 스윙)   | Swing Agent | 중 |
| F (매크로 심화) | Macro Agent | 높 (Gamma 확장) |
