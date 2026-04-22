# packages/adapters

> 외부 데이터 소스에 대한 통일된 접근 레이어.

## 채택된 소스

| Adapter | 역할 | 우선순위 | 레거시 참고 |
|---|---|---|---|
| `kis/` | 한국투자증권 — 주문·체결·시세 (Execute 탭) | P0 | `legacy/kis_korea_investment/` |
| `kiwoom/` | 주가·거래량 (EOD) | P0 | `legacy/company_credit/` |
| `dart/` | 공시·재무 | P1 | `legacy/dart_analysis/` |
| `naver/` | 재무 보조 (Kiwoom REST 재무 없음) | P1 | `legacy/company_credit/` |
| `fred/` | 미국 매크로 | P2 | — |
| `ecos/` | 한국은행 매크로 | P2 | — |
| `kosis/` | 통계청 | P3 | — |
| `eia/`  | 유가·에너지 | P3 | — |
| `exim/` | 수출입은행 환율 | P3 | — |

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
Phase 3: kis/ + kiwoom/ 실제 구현 (legacy 포팅)
Phase 4: dart/ + naver/
Phase 5+: 나머지 매크로 어댑터
