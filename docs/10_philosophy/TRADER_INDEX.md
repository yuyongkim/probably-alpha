# TRADER_INDEX.md
> Market Wizards 3부작 트레이더 빠른 찾아보기 인덱스.
> 원문: `MARKET_WIZARDS_KIWOOM_CONDITIONS_KO.md` (보존 원전)

---

## 전략군 요약

| 전략군 | 핵심 개념 | 대표 트레이더 |
|--------|----------|-------------|
| 추세추종 | MA 정배열, 신고가 돌파, ATR 사이징 | Dennis, Seykota, Hite, Bielfeldt, Jones |
| 성장 모멘텀 | 52주 고가 근접, RS 상위, 실적 가속, VCP | O'Neil, Ryan, Driehaus, Minervini, Cohen, Walton |
| 단기 스윙 | EMA10, RSI, ADX, 좁은 레인지 | Schwartz, Raschke, Trout |
| 역발상/가치 | PBR/PER 저평가, 극단적 하락, 촉매 | Rogers, Steinhardt, Okumus |
| 글로벌 매크로 | 유동성, 금리, 환율 | Kovner, Druckenmiller, Weiss |
| 공매도 | 실적 둔화, 과대평가, 차트 붕괴 | Galante |

---

## 1. Market Wizards (1989)

| # | 트레이더 | 스타일 | SEPA 매핑 |
|---|---------|--------|---------|
| 1-1 | Michael Marcus | 펀더멘털+기술 혼합 | Alpha (20/60/120 정배열) |
| 1-2 | Bruce Kovner | 글로벌 매크로 | Gamma (매크로) |
| 1-3 | Richard Dennis | 터틀 추세추종, 20/55일 돌파 | Alpha (추세추종) |
| 1-4 | Paul Tudor Jones | 200MA 필터, 손실 우선 | Alpha (200MA 필터) |
| 1-5 | Ed Seykota | 시스템 추세추종, EMA 크로스 | Alpha+Omega (규칙 준수) |
| 1-6 | Larry Hite | 1% 룰, 시스템 추세추종 | Delta (리스크 사이징) |
| 1-7 | William O'Neil | CAN SLIM, 신고가+실적 | Alpha+Gamma (SEPA 기반) |
| 1-8 | David Ryan | VCP/컵앤핸들 | Beta (VCP 수축) |
| 1-9 | Marty Schwartz | EMA10, 단기 모멘텀 | Beta 보완 (스윙) |
| 1-10 | James B. Rogers Jr. | 역발상 가치 | Value Agent (향후) |
| 1-11 | Mark Weinstein | 저변동성 스퀴즈 | Beta (수축 패턴) |
| 1-13 | Gary Bielfeldt | 집중+피라미딩 | Alpha (추세+피라미딩) |
| 1-14 | Michael Steinhardt | Variant Perception | Value Agent (향후) |

## 2. New Market Wizards (1992)

| # | 트레이더 | 스타일 | SEPA 매핑 |
|---|---------|--------|---------|
| 2-1 | Stan Druckenmiller | 매크로+유동성 | Gamma (매크로/외인수급) |
| 2-2 | William Eckhardt | 퀀트 추세추종, RR 3:1 | Delta (R:R 규칙) |
| 2-3 | Bill Lipschutz | FX 매크로, RR 3:1 | Delta (R:R 3:1) |
| 2-5 | Richard Driehaus | 실적 서프라이즈 | Gamma (실적 가속) |
| 2-6 | Linda Bradford Raschke | NR7, 1-2-3 패턴 | Beta (NR7/좁은레인지) |
| 2-8 | Monroe Trout | ATR 필터 | Delta (ATR 사이징) |
| 2-9 | Tom Basso | 변동성 조정 사이징 | Delta (변동성 사이징) |

## 3. Stock Market Wizards (2001)

| # | 트레이더 | 스타일 | SEPA 매핑 |
|---|---------|--------|---------|
| 3-1 | **Mark Minervini** | **SEPA, TT 8조건, VCP** | **Alpha+Beta+Omega (핵심)** |
| 3-2 | Steve Cohen | O'Neil 기반, Stage 2 | Alpha (Stage 2 필터) |
| 3-3 | Stuart Walton | IT 성장주 | Alpha+Gamma |
| 3-4 | Dana Galante | 공매도 전문 | Short Agent (향후) |
| 3-5 | Ahmet Okumus | 깊은 가치+촉매 | Value Agent (향후) |

---

## SEPA 에이전트 ↔ 트레이더 매핑

| Agent | 주요 트레이더 | 핵심 원칙 |
|-------|------------|---------|
| Alpha | Minervini, O'Neil, Jones | TT 8조건 + RS 상위 |
| Beta  | Minervini(VCP), Ryan, Weinstein, Raschke | 변동성 수축 패턴 |
| Gamma | O'Neil(C,A), Driehaus, Druckenmiller | 실적 가속 + 매크로 |
| Delta | Hite(1%), Lipschutz(3:1), Basso, Dennis(ATR) | 리스크 선행 통제 |
| Omega | Seykota(규칙), Eckhardt(불편한 결정) | 최종 선정 |

---

## 미구현 / 향후 확장

| 전략 | 트레이더 | 에이전트 |
|------|---------|---------|
| 역발상/가치 | Rogers, Steinhardt, Okumus | Value Agent |
| 공매도 | Galante | Short Agent |
| 스윙/단기 | Schwartz, Raschke, Trout | Swing Agent |
| 매크로 심화 | Kovner, Druckenmiller | Macro Agent (Gamma 확장) |
