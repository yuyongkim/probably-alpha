# packages/adapters

> 외부 데이터 소스에 대한 통일된 접근 레이어.

## 데이터 소스 정책 (2026-04-22 확정)

**KIS = 시세·종목마스터·주문의 단일 소스.** 국내주식, 해외주식(미/일/홍콩/상해/베트남), 채권, 선물옵션, ELW, ETF 전부 KIS에서. Kiwoom/Yahoo 레이어 제거.

**DART = 공시·PIT 재무의 단일 소스.** KIS 재무는 요약만 제공 → DART가 주력, KIS 재무는 크로스체크용.

**매크로는 공식 정부/중앙은행 API만** — FRED, ECOS, EIA, EXIM, KOSIS. 중복 없음.

**네이버 스크래핑 금지** — KIS + DART 조합으로 대체. 약관/안정성 리스크 회피.

## 채택된 소스

| Adapter | 역할 | 우선순위 | 레거시 참고 |
|---|---|---|---|
| `kis/` | **시세·종목·주문 (단일 백본)** — 국내/해외/파생/채권/ETF | **P0** | `legacy/kis_korea_investment/` |
| `dart/` | 공시·PIT 재무 | P0 | `legacy/dart_analysis/` |
| `fred/` | 미국 매크로 | P1 | — |
| `ecos/` | 한국은행 매크로 | P1 | — |
| `kosis/` | 통계청 | P2 | — |
| `eia/`  | 유가·에너지 재고 | P2 | — |
| `exim/` | 수출입은행 환율 | P2 | — |

### Deprecated (legacy 포팅 후 제거)

| Adapter | 대체 | 사유 |
|---|---|---|
| ~~`kiwoom/`~~ | `kis/` | KIS 국내주식 156 API 로 커버. 이중화 불필요 |
| ~~`yahoo/`~~ | `kis/` | KIS 해외주식 30+ API + WebSocket 으로 커버 |
| ~~`naver/`~~ | `kis/` + `dart/` | 스크래핑 회피, 공식 API 만 사용 |

## 공통 계약

모든 어댑터는 다음 인터페이스를 구현해야 한다:

```python
class BaseAdapter:
    source_id: str             # e.g. "kis", "kiwoom", "dart"
    priority: int              # 낮을수록 우선 (1=primary, 2=fallback, ...)

    def healthcheck(self) -> bool: ...
    def close(self) -> None: ...
```

### 규칙

1. **Timeout 필수** — 기본 5s, 환경변수로 오버라이드
2. **Retry 정책** — exponential backoff (max 3회)
3. **Race fallback** — primary 실패 시 priority 순으로 fallback
4. **Source 메타 기록** — 모든 반환 레코드에 `source: {id, fetched_at}` 삽입
5. **Secret 로드** — `settings` 를 import 하고, 누락 시 조기 실패

## 로컬 개발

```python
from ky_adapters.kis import KISAdapter
kis = KISAdapter.from_settings()
kis.healthcheck()
```

## 승격 로드맵

Phase 2 (현재): 디렉터리 + README 뼈대만
Phase 3: **kis/ 실제 구현** — 단일 시세 백본. Kiwoom/Yahoo 어댑터는 만들지 않음.
Phase 4: dart/ — 공시 + PIT 재무
Phase 5+: 매크로 어댑터 (FRED/ECOS/KOSIS/EIA/EXIM)
Phase 6+: `legacy/company_credit/` 에서 Kiwoom 호출부 → KIS 호출부로 리팩터링
