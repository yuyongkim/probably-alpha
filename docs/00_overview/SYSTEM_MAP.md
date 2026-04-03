# SYSTEM_MAP.md
> 전체 시스템 지도. 작업 전 반드시 확인.
> 이 문서는 "어디에 뭐가 있는지"를 알려주는 인덱스이며, 상세 내용은 각 레이어 문서 참조.

---

## 시스템 전체 흐름

```
  [시세 수집]              [분석 파이프라인]           [산출물 제공]
  ───────────             ──────────────             ─────────────
  Kiwoom API              Alpha (추세 필터)          API (FastAPI)
  QuantDB (SQLite)   →    Beta  (VCP 패턴)     →    Frontend (HTML/JS)
  Yahoo Finance           Gamma (실적+매크로)        recommendations.db
  샘플 데이터              Delta (리스크 관리)        daily-signals/
                          Omega (최종 선정)          briefing/report
                          Leader Scan (섹터/주도주)
```

---

## 디렉토리 지도

### 코어 엔진 (`sepa/`)

| 모듈 | 역할 | 핵심 파일 |
|------|------|----------|
| `sepa/agents/` | 에이전트 실행 | `alpha.py`, `beta.py`, `gamma.py`, `delta.py`, `omega.py`, `leaders.py`, `recommender.py` |
| `sepa/analysis/` | 기술적 분석 함수 | `indicators.py`, `patterns.py`, `persistence.py`, `sector_logic.py` |
| `sepa/data/` | 데이터 수집/변환 | `kiwoom.py`, `price_history.py`, `quantdb.py`, `symbols.py`, `universe.py`, `sector_map.py` |
| `sepa/pipeline/` | 파이프라인 오케스트레이션 | `refresh_market_data.py`, `run_after_close.py`, `run_mvp.py`, `run_live_cycle.py`, `backfill_history.py` |
| `sepa/api/` | FastAPI 백엔드 | `app.py`, `routes_public.py`, `routes_admin.py`, `services.py` |
| `sepa/frontend/` | 정적 대시보드 | `index.html`, `js/main.js`, `js/charts.js`, `js/renderers/*.js` |
| `sepa/reporting/` | 브리핑 생성 | `briefing.py` |
| `sepa/storage/` | DB 관리 | `recommendation_store.py` |
| `sepa/wizards/` | Market Wizards 스크리닝 | `wizard_screen.py` |
| `sepa/contracts/` | JSON 스키마 정의 | `gamma_insights.schema.json`, `omega_final_picks.schema.json` |

### 설정 (`config/`)

| 파일 | 용도 |
|------|------|
| `minervini_config.json` | 추천 가중치(0.45/0.20/0.20/0.10/0.05), 게이트 임계값, 리스크 파라미터 |
| `krx_universe.csv` | KRX 종목 유니버스 마스터 |
| `settings.py` | 환경변수 로더, API 키, CORS, 호스트/포트 |

### 스크립트 (`scripts/`)

| 파일 | 용도 |
|------|------|
| `start_local.bat` / `start_local.ps1` | 로컬 전체 시작 (파이프라인 + API + Frontend) |
| `auto_backfill.py` | Windows Task Scheduler용 자동 백필 |
| `generate_debate.py` | 트레이더 토론 데이터 생성 |

### 산출물 (`.omx/artifacts/`)

| 경로 | 내용 |
|------|------|
| `market-data/ohlcv/{SYMBOL}.csv` | 종목별 일봉 (date, close, volume) |
| `market-data/index/{MARKET}.csv` | 시장 지수 (KOSPI, KOSDAQ) |
| `daily-signals/{YYYYMMDD}/` | 일일 분석 결과 전체 |
| `recommendations.db` | 추천 히스토리 SQLite |

---

## 문서 레이어 지도

| Layer | 경로 | 내용 |
|-------|------|------|
| 00 개요 | `docs/00_overview/` | 프로젝트 목적, 이 시스템 맵 |
| 10 철학 | `docs/10_philosophy/` | Minervini 철학, Market Wizards 원전, 전략군 분류 |
| 20 아키텍처 | `docs/20_architecture/` | 에이전트 체인, 스코어링 공식, 백테스트 규칙 |
| 30 데이터 계약 | `docs/30_data_contracts/` | API 스펙, 심볼 매핑, 산출물 스키마 |
| 40 운영 | `docs/40_operations/` | 실행 가이드, 자동화, 일일 운영 |
| 50 제품 | `docs/50_product/` | UI 정보 구조, API 제품 계획 |

---

## API 엔드포인트 지도

| 경로 | 설명 |
|------|------|
| `GET /api/health` | 헬스체크 |
| `GET /api/dashboard` | 전체 대시보드 데이터 |
| `GET /api/leaders/sectors` | 주도 섹터 |
| `GET /api/leaders/stocks` | 주도주 |
| `GET /api/leaders/sectors-grouped` | 섹터별 그룹 |
| `GET /api/alpha` ~ `/api/omega` | 에이전트별 산출물 |
| `GET /api/stock/{symbol}/profile` | 종목 프로필 |
| `GET /api/stock/{symbol}/analysis` | 종목 분석 |
| `GET /api/recommendations/latest` | 최신 추천 |
| `GET /api/recommendations/history` | 추천 히스토리 |
| `GET /api/briefing/latest` | 오늘 브리핑 |
| `GET /api/trader-debate` | 트레이더 토론 |

---

## 데이터 흐름 요약

```
1. 시세 수집 (refresh_market_data.py)
   Kiwoom → QuantDB → Yahoo → 샘플 (폴백 순서)
   → .omx/artifacts/market-data/ohlcv/*.csv

2. 파이프라인 실행 (run_after_close.py)
   Alpha → Beta → Gamma → Delta → Omega
   + Leader Sector/Stock Scan
   + Wizard Screen
   → .omx/artifacts/daily-signals/{YYYYMMDD}/*.json

3. 저장 (recommendation_store.py)
   → .omx/artifacts/recommendations.db

4. 제공 (api/ + frontend/)
   → FastAPI REST API + 정적 대시보드
```

---

## 작업 시 확인 순서

1. 이 파일 (`SYSTEM_MAP.md`)에서 관련 모듈 위치 확인
2. 해당 레이어의 spec 문서 읽기
3. 코드 읽기
4. 변경 후 다운스트림 영향 확인
