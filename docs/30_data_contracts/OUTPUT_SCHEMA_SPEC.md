# OUTPUT_SCHEMA_SPEC.md
> 모든 산출물의 JSON 스키마, 경로, 버전 관리 규칙.

***

## 1. 경로 구조

```
.omx/artifacts/
├── market-data/
│   ├── ohlcv/{SYMBOL}.csv
│   └── index/{MARKET}.csv
├── daily-signals/
│   └── {YYYYMMDD}/
│       ├── alpha-passed.json
│       ├── beta-vcp-candidates.json
│       ├── gamma-insights.json
│       ├── gamma-chem-insights.json
│       ├── delta-risk-plan.json
│       ├── omega-final-picks.json
│       ├── omega-report.html
│       ├── leader-sectors.json
│       ├── leader-stocks.json
│       ├── leader-sectors-grouped.json
│       ├── recommendations.json
│       ├── recommendations-report.html
│       ├── briefing.json
│       ├── briefing.md
│       ├── daily-leaders-report.md
│       ├── wizard-screen.json
│       └── trader-debate.json
├── recommendations.db          (SQLite)
└── audit-logs/
    └── {agent}-{YYYYMMDD}-{HHmmss}.log
```

***

## 2. 스키마 버전 관리

- 모든 산출물 JSON에 `schema_version` 필드를 포함한다.
- 하위 호환 변경: `1.0 → 1.1`처럼 **마이너 버전** 증가.
- 하위 비호환 변경:
  - `1.x → 2.0`처럼 **메이저 버전** 증가.
  - 마이그레이션 가이드 작성 필수.
- 버전 변경 시:
  - 이 문서
  - 관련 에이전트 코드
  - API 라우터
  - 프론트 렌더러
  **동시 업데이트 필수**.

***

## 3. 공통 필드 (모든 산출물 공통 헤더)

```json
{
  "schema_version": "1.0",
  "date": "YYYYMMDD",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "pipeline_run_id": "string",
  "stale_data": false
}
```

- `stale_data`: 전일 캐시 등 신선하지 않은 데이터 사용 시 `true`.

***

## 4. 파일별 스키마 상세

여기서는 헤더만 정의하고, 상세 구조는 각 스펙 문서를 따른다.

- `alpha-passed.json` / `beta-vcp-candidates.json` / `gamma-*` / `delta-risk-plan.json` / `omega-final-picks.json`
  → `docs/20_architecture/SEPA_OMX_MASTER_SPEC.md` 4장 참조

- `leader-sectors.json` / `leader-stocks.json`
  → `docs/20_architecture/LEADER_SCORING_SPEC.md` 1/2장 참조

- `recommendations.json`
  → `docs/20_architecture/SEPA_OMX_MASTER_SPEC.md` Omega 절 참조

- `briefing.json` / `briefing.md`
  → `sepa/reporting/briefing.py` 구현 참조

- `wizard-screen.json`
  → `sepa/wizards/` 모듈 참조

- `trader-debate.json`
  → `scripts/generate_debate.py` 참조

***

## 5. CSV 데이터 파일 규격

### OHLCV (`market-data/ohlcv/{SYMBOL}.csv`)

```csv
date,close,volume
2026-04-01,72300,15234000
2026-04-02,73100,18456000
```

- `date`: ISO 형식 (YYYY-MM-DD)
- `close`: 종가 (원)
- `volume`: 거래량 (주)
- 정렬: 날짜 오름차순

### 시장 지수 (`market-data/index/{MARKET}.csv`)

```csv
date,close,volume
2026-04-01,2687.45,523000000
```

- KOSPI, KOSDAQ 등 벤치마크 지수
