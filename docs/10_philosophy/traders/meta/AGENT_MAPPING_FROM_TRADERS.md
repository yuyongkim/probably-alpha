# 에이전트 매핑: 트레이더 → SEPA 에이전트

> 각 SEPA 에이전트(Alpha~Omega)에 영향을 준 트레이더와 그 원칙.

---

## Alpha (추세 필터)

Alpha는 "매수할 자격이 있는 종목"을 걸러내는 첫 관문.

| 원칙 | 트레이더 | 구현 |
|------|---------|------|
| TT 8조건 (정배열+RS+52주) | Minervini | `alpha.py` checks c1~c8 |
| 200MA 필터 | Jones | check c8: close > SMA200 |
| 20일 채널 돌파 | Dennis | backtest preset `require_20d_breakout` |
| RS 상위만 진입 | O'Neil, Driehaus | check c7: RS >= threshold |
| CAN SLIM의 N (신고가) | O'Neil | check c6: close >= 75% of 52w high |
| Stage 2만 진입 | Weinstein, Cohen | 정배열 = Stage 2 |

## Beta (패턴/타이밍)

Beta는 "지금이 매수 타이밍인가"를 판단.

| 원칙 | 트레이더 | 구현 |
|------|---------|------|
| VCP (변동성 수축) | Minervini | `beta.py` wave detection |
| 컵앤핸들 | Ryan, O'Neil | `patterns.py` detect_cup_with_handle |
| NR7/좁은 레인지 | Raschke | backtest preset `require_volatility_contraction` |
| 거래량 건조 | Minervini, Weinstein | `beta.py` volume_dryup |
| 볼린저밴드 수축 | Weinstein | factor `volatility_contraction` |
| 돌파 거래량 급증 | O'Neil, Dennis | backtest preset `require_volume_expansion` |

## Gamma (실적/매크로)

Gamma는 펀더멘털과 매크로 환경을 확인.

| 원칙 | 트레이더 | 구현 |
|------|---------|------|
| EPS 가속 (QoQ/YoY) | O'Neil, Driehaus | `gamma.py` eps growth |
| 매출 성장 | O'Neil (CAN SLIM의 A) | gamma score |
| ROE/영업이익률 | Greenblatt | gamma fq_bonus |
| 매크로 유동성 방향 | Druckenmiller, Dalio | gamma macro_score |
| 화학 업황 (유가/스프레드) | — | gamma chem_bonus |
| 외인/기관 수급 | Camillo, Shapiro | 향후 확장 |

## Delta (리스크/사이징)

Delta는 "얼마나, 어디서 손절할 것인가"를 결정.

| 원칙 | 트레이더 | 구현 |
|------|---------|------|
| 7~8% 손절 | Minervini, O'Neil | `delta.py` stop_loss_pct |
| 1% 리스크 룰 | Hite | position sizing |
| ATR 기반 사이징 | Dennis (터틀), Basso | backtest engine |
| R:R 최소 1.5~3:1 | Eckhardt, Lipschutz | `delta.py` rr_ratio |
| 일일 손실 한도 | Benedict | backtest stop |
| Kelly criterion | Thorp | 향후 구현 |

## Omega (최종 선택)

Omega는 "규칙을 지키고 최종 결정을 내리는" 단계.

| 원칙 | 트레이더 | 구현 |
|------|---------|------|
| 규칙 절대 준수 | Seykota | omega 결정 일관성 |
| 불편한 결정이 맞는 결정 | Eckhardt | 감정 반대로 행동 |
| 섹터 분산 | Hite, Platt | sector_limit |
| 최종 1~3종목 선정 | — | `omega.py` top_n |
| 이유(reason) 명시 | — | 모든 추천에 사유 필수 |

## 향후 에이전트

| 에이전트 | 트레이더 | 역할 |
|---------|---------|------|
| Value Agent | Greenblatt, Okumus, Steinhardt | 저평가+촉매 종목 발굴 |
| Short Agent | Galante, Guazzoni | 공매도 후보 |
| Swing Agent | Schwartz, Raschke | 단기 스윙 시그널 |
| Macro Agent | Dalio, Druckenmiller | 매크로 환경 판단 |
