# packages/adapters

> 외부 데이터 소스에 대한 통일된 접근 레이어.

## 데이터 소스 정책 (2026-04-22 확정)

**KIS = 시세·종목마스터·주문의 단일 소스.** 국내주식, 해외주식(미/일/홍콩/상해/베트남), 채권, 선물옵션, ELW, ETF 전부 KIS에서. Kiwoom/Yahoo 레이어 제거.

**DART = 공시·PIT 재무의 단일 소스.** KIS 재무는 요약만 제공 → DART가 주력, KIS 재무는 크로스체크용.

**매크로는 공식 정부/중앙은행 API만** — FRED, ECOS, EIA, EXIM, KOSIS. 중복 없음.

**네이버 스크래핑 금지** — KIS + DART 조합으로 대체.

## 채택된 소스

| Adapter | 역할 | 우선순위 | 상태 |
|---|---|---|---|
| `kis/` | 시세·종목·주문 (단일 백본) | P0 | **skeleton** — 키 없음 |
| `dart/` | 공시·PIT 재무 | P0 | 구현 |
| `fred/` | 미국 매크로 | P1 | 구현 |
| `ecos/` | 한국은행 매크로 | P1 | 구현 |
| `kosis/` | 통계청 | P2 | 구현 |
| `eia/`  | 유가·에너지 재고 | P2 | 구현 |
| `exim/` | 수출입은행 환율 | P2 | 구현 |

## 공통 계약

모든 어댑터는 `ky_adapters.base.BaseAdapter` 를 상속한다:

```python
class BaseAdapter:
    source_id: str
    priority: int

    def healthcheck(self) -> dict: ...   # {ok, source_id, latency_ms, last_error, ...}
    def close(self) -> None: ...
```

공통 에러 타입: `AdapterError`, `AuthError`, `RateLimitError`.
HTTP 호출은 `base.http_request()` 가 담당 (timeout 10s, retry 3회 exp backoff).

## 사용 예

### FRED
```python
from datetime import date
from ky_adapters.fred import FREDAdapter

with FREDAdapter.from_settings() as fred:
    print(fred.healthcheck())
    obs = fred.get_series("GDP", start=date(2020, 1, 1), end=date.today())
    print(obs[-1])   # Observation(series_id='GDP', date='2024-01-01', value=..., unit=...)
```

### ECOS (한국은행)
```python
from ky_adapters.ecos import ECOSAdapter

with ECOSAdapter.from_settings() as ecos:
    obs = ecos.get_series("722Y001", "0101000", "20240101", "20241231", freq="D")
    print(obs[:3])
```

### DART (공시)
```python
from datetime import date, timedelta
from ky_adapters.dart import DARTAdapter

with DARTAdapter.from_settings() as dart:
    recent = dart.list_disclosures(
        corp_code="00126380",
        start=date.today() - timedelta(days=30),
        end=date.today(),
        page_count=10,
    )
    for f in recent:
        print(f.filed_at, f.corp_name, f.report_name)
```

### EIA (원유)
```python
from ky_adapters.eia import EIAAdapter

with EIAAdapter.from_settings() as eia:
    obs = eia.get_series("PET.WCESTUS1.W")   # 미국 주간 원유 재고
```

### EXIM (환율)
```python
from datetime import date
from ky_adapters.exim import EXIMAdapter

with EXIMAdapter.from_settings() as exim:
    rates = exim.get_rates(search_date=date.today())
    for r in rates:
        print(r.cur_unit, r.cur_nm, r.deal_bas_r)
```

### KIS (스켈레톤)
```python
from ky_adapters.kis import KISAdapter

kis = KISAdapter.from_settings()
print(kis.healthcheck())  # {ok: False, last_error: "KIS_APP_KEY not configured"}
```

## 규칙

1. **Timeout 필수** — 기본 10s
2. **Retry 정책** — exponential backoff (max 3회), 5xx/429 만 재시도
3. **Secret 로드** — `from_settings()` 팩토리가 `~/.ky-platform/shared.env` 에서 주입
4. **파일 크기** — 어댑터 모듈은 300 줄 이하 유지. 초과 시 하위 모듈 분리.
5. **네이버/야후/키움 금지** — 정책 위반
