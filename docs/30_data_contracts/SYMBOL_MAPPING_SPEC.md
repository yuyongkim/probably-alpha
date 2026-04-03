# SYMBOL_MAPPING_SPEC.md
> 종목 코드 체계 및 매핑 규칙 정의.
> 관련 코드: `sepa/data/symbols.py`, `sepa/data/universe.py`

---

## 1. 코드 체계

| 소스      | 형식           | 예시                  |
|-----------|---------------|-----------------------|
| KRX       | 6자리 숫자     | `005930`              |
| 키움 OpenAPI | 6자리 숫자  | `005930`              |
| Yahoo Finance | 6자리 + 시장 | `005930.KS` (KOSPI), `247540.KQ` (KOSDAQ) |
| 내부 표준  | 6자리 숫자     | `005930`              |

---

## 2. 변환 규칙

### 내부 → Yahoo Finance

```python
def to_yahoo_ticker(symbol: str) -> str:
    market = infer_market(symbol)
    if market == "KOSPI":
        return f"{symbol}.KS"
    elif market == "KOSDAQ":
        return f"{symbol}.KQ"
    return symbol
```

### Yahoo Finance → 내부

```python
def from_yahoo_ticker(ticker: str) -> str:
    return ticker.replace(".KS", "").replace(".KQ", "")
```

### 내부 → 키움

```python
def to_kiwoom_symbol(symbol: str) -> str:
    # .KS/.KQ 접미사 제거, 6자리 숫자만 반환
    return symbol.replace(".KS", "").replace(".KQ", "").zfill(6)
```

### 시장 구분

```python
def infer_market(symbol: str) -> str:
    # 6자리 숫자 가정
    # KOSPI / KOSDAQ 매핑은 KRX 종목마스터 기준
    if symbol in kospi_set:
        return "KOSPI"
    elif symbol in kosdaq_set:
        return "KOSDAQ"
    return "UNKNOWN"
```

- 실제 KOSPI/KOSDAQ 구분은 **KRX 종목마스터 파일** 기준으로 전처리.

---

## 3. 제외 대상 규칙

유니버스/백테스트에서 제외할 종목 유형:

- ETF:
  - 종목명에 `ETF` 또는 `Index` 포함
  - 또는 KRX 제공 **ETF 리스트** 기준
- ETN:
  - 종목명에 `ETN` 포함
- SPAC:
  - 종목명에 `기업인수목적` 포함
- 관리종목:
  - KRX 관리종목 리스트 참조
- 거래정지:
  - 최근 5일 연속 `거래량 = 0`

관련 코드:
- `sepa/data/universe.py`

---

## 4. 관련 파일

- `sepa/data/symbols.py`  → 변환 함수 구현
- `sepa/data/universe.py` → 유니버스 필터 적용
- `config/krx_universe.csv` → KRX 종목마스터
