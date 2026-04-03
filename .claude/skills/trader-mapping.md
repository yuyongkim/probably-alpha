# trader-mapping.md
> Market Wizards 트레이더들의 철학을 SEPA/에이전트/조건식에 매핑하는 스킬.
> Source of Truth는 `docs/10_philosophy/TRADER_INDEX.md` 및 `STRATEGY_FAMILIES.md`.

---

## 1. 이 스��을 언제 쓸 것인가

- "��� 트레이더의 철학이 우리 시스템에 어디 반영되어 ���지?"
- "새 전략/필터를 추가하는데, 어떤 트레이더 철학에 가까운지 알고 싶다"
- "Minervini 말고 다른 트레이더의 조건을 Alpha/Beta에 녹이고 싶다"
- "TRADER_INDEX.md 업데이트가 필요한데, 정합성 확인해줘"

---

## 2. 작업 개요

1. 트레이더 철학 확인 (원전: `MARKET_WIZARDS_KIWOOM_CONDITIONS_KO.md`)
2. 해당 철학이 어느 전략군(A~G)에 속하는지 분류 (`STRATEGY_FAMILIES.md`)
3. 현재 SEPA 에이전트 중 어디에 매핑되는지 확인 (`TRADER_INDEX.md`)
4. 매핑 결과를 인덱스에 반영하거나, 미구현 시 향후 확장 목록에 추가

---

## 3. 전략군 분류 기준

| 전략군 | 핵심 키워드 | SEPA 에이전트 |
|--------|-----------|-------------|
| A: 추세추종 | MA 정배열, 신고가, ATR | Alpha, Delta |
| B: 성장 모멘텀 | RS 상위, EPS 가속, VCP | Alpha, Beta, Gamma |
| C: 단기 스윙 | EMA10, NR7, RSI | Beta 보완, Swing Agent (향후) |
| D: 역발상/가치 | PBR/PER 저평가, 촉매 | Value Agent (향후) |
| E: VCP/수축 돌파 | 볼린저 수축, 거래량 건조 | Beta 핵심 |
| F: 글로벌 매크로 | 금리, 환율, 유동성 | Gamma, Macro Agent (향후) |
| G: 공매도 | 실적 둔화, 차트 붕괴 | Short Agent (향후) |

---

## 4. 매핑 작업 시 규칙

- 원전(`MARKET_WIZARDS_KIWOOM_CONDITIONS_KO.md`)은 절대 축약/삭제/대체하지 않는다.
- `TRADER_INDEX.md`와 `STRATEGY_FAMILIES.md`는 원전의 **인덱스 역할만** 한다.
- 새 트레이더 추가 시:
  1. 원전에 조건식/철학 원문 추가
  2. 전략군 분류 → `STRATEGY_FAMILIES.md` 업데이트
  3. 에이전트 매핑 → `TRADER_INDEX.md` 업데이트

---

## 5. 금지 사항

- 트레이더 철학을 자의적으로 해석하여 조건식을 만들지 않는다.
- 원전에 없는 트레이더를 인덱스에 추가하지 않는다.
- 매핑이 불확실할 때 "향후 확장"으로 보류하되, 확정된 것처럼 코드에 반영하지 않는다.
