# packages/core

> 데이터 코어. 모든 도메인 서비스가 의존하는 순수 데이터·계산 레이어.

## 모듈

- `ky_core.storage` — SQLite-backed persistence layer (SQLAlchemy 2.x)
- `ky_core.chartist` — 기존 차트 관련 유틸 (placeholder)

## storage 스키마

기본 DB 경로: `~/.ky-platform/data/ky.db` (`KY_DB_PATH` 환경변수로 오버라이드).

### `observations`
매크로 타임시리즈 단위 레코드. FRED/ECOS/EIA/EXIM 모두 여기로 들어옴.

| column | type | note |
|---|---|---|
| id | INTEGER | PK |
| source_id | VARCHAR(32) | `fred`/`ecos`/`eia`/`exim` 등 |
| series_id | VARCHAR(128) | 소스별 시리즈 식별자 (ECOS는 `"722Y001/0101000"` 형식) |
| date | VARCHAR(10) | ISO YYYY-MM-DD |
| value | FLOAT | NULL 허용 (결측) |
| unit | VARCHAR(64) | 단위 문자열 |
| meta | JSON | 소스별 확장 필드 |
| fetched_at | DATETIME | 수집 시각 (UTC) |
| owner_id | VARCHAR(32) | 멀티테넌시 (기본 `"self"`) |

UNIQUE(`source_id`, `series_id`, `date`, `owner_id`) — upsert 키.

### `filings`
DART 공시 레코드. `meta` 에는 filer 등 확장 정보.

| column | type | note |
|---|---|---|
| id | INTEGER | PK |
| source_id | VARCHAR(32) | `dart` |
| corp_code | VARCHAR(32) | DART corp_code (8자리) |
| receipt_no | VARCHAR(32) | DART 접수번호 (PK-성분) |
| filed_at | VARCHAR(10) | ISO YYYY-MM-DD |
| type | VARCHAR(128) | 보고서 종류 (`report_nm`) |
| summary | TEXT | 요약/회사명 |
| meta | JSON | 확장 |
| fetched_at | DATETIME | |
| owner_id | VARCHAR(32) | |

UNIQUE(`source_id`, `receipt_no`, `owner_id`).

### `universe`
종목 마스터 (KIS 구현 후 채움).

| column | type | note |
|---|---|---|
| id | INTEGER | PK |
| ticker | VARCHAR(32) | 종목코드 |
| market | VARCHAR(16) | KOSPI/KOSDAQ/NASDAQ/... |
| name | VARCHAR(128) | |
| sector | VARCHAR(64) | |
| meta | JSON | |
| updated_at | DATETIME | |
| owner_id | VARCHAR(32) | |

UNIQUE(`ticker`, `market`, `owner_id`).

## 사용 예

```python
from ky_core.storage import Repository

repo = Repository(owner_id="self")

# upsert (adapter rows로부터)
from ky_adapters.fred import FREDAdapter
with FREDAdapter.from_settings() as fred:
    rows = [o.as_row() for o in fred.get_series("GDP", "2020-01-01", "2025-01-01")]
repo.upsert_observations(rows)

# read
latest = repo.latest_observation("fred", "GDP")
recent = repo.get_observations("fred", "GDP", limit=10)
```

## 원칙

- I/O 없음 — 외부 API 호출은 `packages/adapters/` 로 분리
- 결정적 함수 선호
- 모든 함수는 `owner_id` 맥락을 받도록 설계
