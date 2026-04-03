# PORTFOLIO_LIFECYCLE_SPEC.md
> 전략/포트 객체의 라이프사이클(생성~백테스트~모의운용~보관) 정의.

---

## 1. 개념 정의

### 1.1 Strategy vs Portfolio

- **Strategy**:
  - "룰/로직/파라미터"의 묶음.
  - 동일 전략으로 여러 기간/유니버스에 백테스트 가능.
- **Portfolio (Port)**:
  - 특정 전략을 특정 기간/자본/설정으로 운용한 결과.
  - 백테스트 포트, 모의운용 포트, 실거래 포트를 동일 개념으로 다룸.

예) Strategy: "SEPA-Leader-KOSDAQ"
    Portfolio: "SEPA-Leader-KOSDAQ / 2021~2025 / 1억 / 월간 리밸런싱"

---

## 2. 상태(State) 정의

포트는 다음 상태 중 하나에 있다.

1. `DRAFT`
   - 전략은 선택/작성했으나 백테스트를 아직 안 돌린 상태
2. `BACKTESTED`
   - 하나 이상의 backtest run이 연결된 상태
3. `PAPER`
   - 모의운용 중인 상태 (실시간/일일 업데이트)
4. `LIVE`
   - (향후) 실거래 계좌와 연동된 상태
5. `ARCHIVED`
   - 더 이상 사용하지 않지만 기록 보존용으로 남겨둔 상태

---

## 3. 상태 전이

### 3.1 전이 다이어그램 (개념)

```text
[DRAFT] --(백테스트 실행)--> [BACKTESTED] --(모의운용 시작)--> [PAPER] --(실거래 연결)--> [LIVE]
   ^                                |
   |                                +--(아카이브)--> [ARCHIVED]
   +--------------(삭제/아카이브)--------------------^
```

### 3.2 이벤트 정의

- `create_portfolio(strategy_id, params)`:
  - DRAFT 포트 생성
- `run_backtest(portfolio_id, period, capital, params)`:
  - BACKTESTED 상태로 진입
- `start_paper_trading(portfolio_id)`:
  - PAPER 상태로 전환 (포트 상태를 실시간/일일로 업데이트)
- `archive_portfolio(portfolio_id)`:
  - ARCHIVED로 전환

---

## 4. 포트 속성

각 포트는 최소한 다음 속성을 가진다.

- 메타:
  - `id`
  - `name`
  - `strategy_id`
  - `state` (위 상태 중 하나)
- 설정:
  - `initial_capital`
  - `rebalance_frequency`
  - `universe_filter`
  - `risk_limits` (1종목당 최대 손실 등)
- 이력:
  - `backtest_runs`: run_id 리스트
  - `paper_history`: PAPER 상태에서의 자산 곡선
  - `live_history`: LIVE 상태에서의 자산 곡선 (향후)

---

## 5. UI 상 표현

### 5.1 포트 리스트

- 컬럼:
  - 포트 이름
  - 전략 이름
  - 상태 (DRAFT/BACKTESTED/PAPER/LIVE)
  - 대표 성과 (최근 run 기준 CAGR/MDD)

### 5.2 상태별 UI 뱃지

| 상태 | 색상 | 의미 |
|------|------|------|
| DRAFT | 회색 | 아직 테스트 안 함 |
| BACKTESTED | 파란색 | 백테스트 완료 |
| PAPER | 노란색 | 모의운용 중 |
| LIVE | 녹색 | 실거래 연동 |
| ARCHIVED | 어두운 회색 | 보관 |
