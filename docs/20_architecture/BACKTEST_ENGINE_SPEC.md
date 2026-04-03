# BACKTEST_ENGINE_SPEC.md
> SEPA 기반 포트폴리오 백테스트 엔진 설계서.
> "일자 단위, 이벤트 드리븐 스타일" 엔진을 기본으로 한다.

---

## 1. 목표와 범위

### 1.1 목표

- **내가 매일 쓰는** 전략 백테스트 엔진을 만든다.
- 대상:
  - SEPA 리더 섹터/리더 종목 전략
  - 향후 Value/Short/Swing 전략도 동일 엔진으로 돌릴 수 있게 설계
- 레벨:
  - **일봉 단위, 포트폴리오 단위, 이벤트 드리븐 스타일**
  - 실시간/틱 수준은 범위 밖

### 1.2 범위

이 문서는 다음을 정의한다.

- 엔진 루프 구조 (날짜/전략/포트폴리오)
- 주요 객체와 역할 (Portfolio, Strategy, Execution, DataFeed)
- 상태 전이 (신호 → 주문 → 체결 → 포지션 → 성과)
- 설정 파라미터 (리밸런싱, 비용, 제약 조건)
- 출력(결과) 종류와 최소 요구 사항

구현 세부 코드/라이브러리는 별도 Python 모듈에서 다룬다.

---

## 2. 엔진 아키텍처 개요

### 2.1 엔진 타입

- **Event-driven, Daily bar 기반** 엔진
  - 각 "일자"를 이벤트로 보고, 순차적으로 처리
  - 벡터화(한 번에 전체 기간 계산)보다 **직관/디버깅**을 우선
- 핵심 이벤트:
  - `MARKET_OPEN(date)`
  - `BEFORE_SIGNAL(date)`
  - `AFTER_SIGNAL(date)`
  - `BEFORE_EXECUTION(date)`
  - `AFTER_EXECUTION(date)`
  - `MARKET_CLOSE(date)`

### 2.2 주요 컴포넌트

- `DataFeed`
  - 심볼별 일봉 가격/거래량/재무정보 가져오기
- `Strategy`
  - 주어진 날짜/포트폴리오/데이터에서 "신호"를 생성
- `Portfolio`
  - 현금, 포지션, 주문, 체결 기록 관리
- `Execution`
  - 신호/주문을 실제 체결 가격으로 변환
- `BacktestEngine`
  - 위 컴포넌트들을 조립하여 날짜별 루프를 돌림

---

## 3. 루프 구조

### 3.1 고수준 의사코드

```text
for date in trading_calendar[start:end]:
    DataFeed.load(date)
    Portfolio.on_market_open(date)

    # 1) 신호 생성
    signals = Strategy.generate_signals(date, DataFeed, Portfolio)
    Portfolio.register_signals(date, signals)

    # 2) 주문 생성 (포지션/리스크 고려)
    orders = Portfolio.generate_orders_from_signals(date)
    Portfolio.register_orders(date, orders)

    # 3) 체결
    fills = Execution.fill_orders(date, orders, DataFeed)
    Portfolio.apply_fills(date, fills)

    # 4) 포지션/현금/자산 계산
    Portfolio.update_positions(date, DataFeed)
    Portfolio.update_metrics(date, benchmark_data)

    Portfolio.on_market_close(date)
```

### 3.2 신호 → 주문 → 체결

- **Signal**: 단순 "사고/팔고/홀딩" 혹은 목표 비중 등
- **Order**: 실제 주문량/방향/가격 조건을 가진 객체
- **Fill**: 주문이 체결된 결과 (수량/가격/비용)

엔진은 항상 이 순서를 지킨다:

1. 전략은 **Signal**만 만든다 (포지션 사이징/체결은 전략 밖).
2. 포트폴리오가 Signal을 받아 Order로 변환한다.
3. Execution 모듈이 Order를 Fill로 변환한다.

---

## 4. 주요 객체 정의

### 4.1 Strategy

역할:

- 유니버스와 데이터, 현재 포트 상태를 보고 **오늘 할 행동을 제안**.
- SEPA/Alpha/Beta/Gamma/Delta/Omega 등의 규칙을 구현.

인터페이스(개념):

```python
class Strategy:
    def generate_signals(self, date, data_feed, portfolio) -> list[Signal]:
        ...
```

제약:

- 미래 데이터 사용 금지 (현재 날짜 이전 데이터만 사용).
- 체결 가정/비용은 Strategy 내부에 두지 않는다.

---

### 4.2 Portfolio

역할:

- 현금 잔고, 종목별 포지션, 주문, 체결, 거래 로그, 자산 곡선을 관리.
- 리스크 규칙(최대 종목 수, 섹터 비중, 1종목당 손실 한도 등)을 적용.

핵심 속성:

- `cash`
- `positions`: {symbol -> Position}
- `open_orders`: list[Order]
- `trades`: list[Trade]
- `equity_curve`: {date -> equity}

핵심 메서드(개념):

```python
class Portfolio:
    def register_signals(self, date, signals): ...
    def generate_orders_from_signals(self, date): ...
    def apply_fills(self, date, fills): ...
    def update_positions(self, date, data_feed): ...
    def update_metrics(self, date, benchmark_data): ...
```

---

### 4.3 Execution

역할:

- 주문을 체결 가격/수량으로 바꾸는 모듈.
- **체결 룰**과 **비용(수수료/슬리피지/세금)**을 한 곳에 모아 관리.

체결 가정:

- 기본: **next-open 체결**
- 옵션:
  - same-close (테스트용)
  - next-close

비용:

- 수수료, 슬리피지, 세금은 항상 Execution에서 적용한다.

---

### 4.4 DataFeed

역할:

- 주어진 날짜/심볼에 대해 필요한 필드를 제공.
- 가격/거래량/거래대금/재무지표/섹터 정보 등을 가져오는 통합 레이어.

개념:

```python
class DataFeed:
    def get_bar(self, symbol, date) -> Bar: ...
    def get_history(self, symbol, date, lookback) -> list[dict]: ...
    def get_universe(self, date) -> list[str]: ...
    def get_benchmark_return(self, date) -> float: ...
```

---

## 5. 파라미터 & 규칙

### 5.1 글로벌 파라미터

- 기간:
  - `start_date`, `end_date`
- 유니버스 필터:
  - 시총, 거래대금, ETF/ETN/관리종목 제외 등
- 리밸런싱:
  - `rebalance_frequency`: daily / weekly / monthly
- 비용:
  - `commission_rate_buy`, `commission_rate_sell`
  - `slippage_rate`
  - `tax_rate_sell`

### 5.2 리스크/제약

- 최대 보유 종목 수
- 섹터별 최대 종목/비중
- 1종목당 최대 손실(% of equity)

이 값들은 엔진의 `config` 객체로 관리한다.

---

## 6. 출력 및 저장

엔진은 백테스트 한 번당 **하나의 run**을 생성한다.

각 run은 최소한 다음 산출물을 가진다:

- `backtest_run` 요약:
  - run_id, 전략명, 기간, 파라미터, 요약 지표(CAGR, MDD, Sharpe 등)
- `equity_curve`:
  - 날짜별 자산 가치/벤치마크
- `trades`:
  - 각 거래의 날짜, 심볼, 수량, 가격, 비용, 이유
- `orders`:
  - 주문 생성 시점, 체결 여부, 부분 체결 등 (필요 시)
- `positions`:
  - 날짜별 포지션 상태 (심볼/수량/평단 등)

구체적인 JSON 구조는 `docs/30_data_contracts/REPORTING_SCHEMA_SPEC.md`에서 정의한다.
