# CLAUDE.md
> Claude Code가 매 세션 시작 시 가장 먼저 읽는 프로젝트 헌법.
> 세부 내용은 아래 Source of Truth 문서에 있습니다.

---

## 프로젝트 정체성

이 프로젝트는 **한국 주식시장 주도주/주도섹터 탐지 엔진**입니다.
Minervini SEPA 전략을 OmX Multi-Agent 아키텍처로 구현하며,
Market Wizards 트레이더들의 철학을 통합한 재현 가능한 의사결정 파이프라인을 만듭니다.

핵심 목표:
1. 오늘 종가 기준 주도 섹터 Top N 탐지
2. 주도 섹터 내 주도주 Top M 탐지
3. Alpha -> Beta -> Gamma -> Delta -> Omega 에이전트 체인으로 최종 1~3종목 추천
4. 재현 가능한 EOD 백테스트 지원
5. Backend API + Frontend Dashboard로 산출물 노출
6. 장기: 구독형 리포트 -> B2B API

---

## Source of Truth 문서 계층

**먼저 읽을 문서:**
- `docs/00_overview/SYSTEM_MAP.md`  ← 전체 지도, 작업 전 반드시 확인

### Layer 00: 개요
- `docs/00_overview/PROJECT_OBJECTIVE_KO.md`
- `docs/00_overview/SYSTEM_MAP.md`

### Layer 10: 전략 철학 (원전 보존 - 절대 삭제/축약 금지)
- `docs/10_philosophy/MARKET_WIZARDS_KIWOOM_CONDITIONS_KO.md`  ← 원전
- `docs/10_philosophy/MINERVINI_PHILOSOPHY_KO.md`
- `docs/10_philosophy/TRADER_INDEX.md`
- `docs/10_philosophy/STRATEGY_FAMILIES.md`

### Layer 20: 아키텍처
- `docs/20_architecture/SEPA_OMX_MASTER_SPEC.md`
- `docs/20_architecture/AGENT_CHAIN.md`
- `docs/20_architecture/LEADER_SCORING_SPEC.md`
- `docs/20_architecture/BACKTEST_RULES.md`

### Layer 30: 데이터 계약
- `docs/30_data_contracts/KIWOOM_ENDPOINT_SPEC.md`
- `docs/30_data_contracts/SYMBOL_MAPPING_SPEC.md`
- `docs/30_data_contracts/OUTPUT_SCHEMA_SPEC.md`

### Layer 40: 운영
- `docs/40_operations/FRONTEND_BACKEND_RUNBOOK_KO.md`
- `docs/40_operations/AUTO_BACKFILL_SETUP_KO.md`
- `docs/40_operations/SAAS_DAILY_OPERATIONS_KO.md`

### Layer 50: 제품/UI
- `docs/50_product/UI_INFORMATION_ARCHITECTURE.md`
- `docs/50_product/API_PRODUCT_PLAN.md`

### Claude Skills / Rules / Agents
- `.claude/rules/strategy.md`      ← 전략 규칙 하드코드
- `.claude/rules/backtest.md`      ← 백테스트 하드 룰
- `.claude/rules/api-contracts.md`
- `.claude/rules/data-integrity.md`
- `.claude/rules/frontend-ui.md`
- `.claude/skills/leader-scan.md`
- `.claude/skills/backtest-review.md`
- `.claude/skills/trader-mapping.md`
- `.claude/skills/kiwoom-adapter-check.md`
- `.claude/agents/sector-rotation.agent.md`
- `.claude/agents/sepa-review.agent.md`
- `.claude/agents/backtest-auditor.agent.md`
- `.claude/agents/frontend-ops.agent.md`

---

## 현재 실행 우선순위 (2026-04)

1. EOD 시세 수집 안정화 (키움 API -> QuantDB -> Yahoo 폴백)
2. 섹터 강도 점수 구현 (`scoring/sector_strength.py`)
3. 주도주 점수 구현 (`scoring/leader_stock.py`)
4. 주도섹터/주도주 일일 스캔
5. EOD 백테스트 엔진 (`backtest/engine.py`)
6. API/프론트 `leaders`, `backtest` 뷰 연결

---

## 절대 원칙 (Hard Rules)

### 전략 무결성
- Minervini SEPA 핵심 규칙 타협 금지
- Alpha/Beta/Gamma/Delta/Omega 역할 경계 유지
- 조건 완화로 종목 수 늘리기 금지
- 모든 산출물 설명 가능해야 함 (블랙박스 금지)

### 백테스트 무결성
- 미래 데이터 사용 절대 금지 (look-ahead bias)
- 신호는 종가 확정 이후 데이터로만 생성
- 체결 가정 항상 명시 (기본: next-open)
- Survivorship bias 명시 (상폐/합병 종목 처리 기록)
- 백테스트 비용 반드시 반영 (수수료+슬리피지+세금)

### 데이터 무결성
- 결측/비정상 응답 방어적 처리 필수
- 제외 종목 및 이유 로그 기록
- 데이터 소스 추상화 (키움/QuantDB/Yahoo 교체 가능)

### 엔지니어링 무결성
- `data` / `factors` / `scoring` / `signals` / `backtest` / `api` / `frontend` 경계 유지
- UI 코드에 비즈니스 로직 혼재 금지
- 새 모듈은 단일 책임
- copy-paste 금지

### 문서 원칙
- Layer 10 원전 문서 절대 축약/삭제/대체 금지
- 요약 문서는 원문을 대체하지 않고 인덱스 역할만
- 새 문서는 기존 문서와 중복 없이 레이어 역할에 맞게 작성

---

## 작업 전 체크리스트

1. `docs/00_overview/SYSTEM_MAP.md` 확인
2. 관련 spec 문서 확인
3. 작업이 어느 레이어에 속하는지 확인
4. 가정 사항 명시
5. 산출물/로그/다운스트림 호환성 검증

---

## 코딩 스타일

- Python: 코어 엔진
- FastAPI: 백엔드 API
- Static HTML/JS: 프론트엔드
- 결정적(deterministic) 함수 선호
- 테스트 가능한 모듈 구조

---

## Commands

```bash
# 로컬 서버 전체 시작 (파이프라인 + API + 프론트엔드)
scripts/start_local.bat

# 시세 데이터만 갱신
python -m sepa.pipeline.refresh_market_data

# 종가 후 전체 파이프라인
python -m sepa.pipeline.run_after_close

# 누락 날짜 백필 (30일)
python scripts/auto_backfill.py

# 특정 기간 백필
python -m sepa.pipeline.backfill_history --date-from 20260315 --date-to 20260325

# 캐시 무시 강제 갱신
SEPA_FORCE_LIVE_REFRESH=1 python -m sepa.pipeline.refresh_market_data
```

## API Endpoints

- `GET /api/health` — 헬스체크
- `GET /api/recommendations/latest` — 오늘 추천 TOP3
- `GET /api/recommendations/history?limit=30` — 추천 히스토리
- `GET /api/briefing/latest` — 오늘 브리핑

## Environment Variables

**필수** (`.env` 파일에 설정):
- `KIWOOM_APP_KEY`, `KIWOOM_SECRET_KEY` — Kiwoom API 인증
- `API_HOST` (기본 127.0.0.1), `API_PORT` (기본 8200), `FRONTEND_PORT` (기본 8280)

**선택**:
- `SEPA_FORCE_LIVE_REFRESH=1` — 캐시 무시 강제 갱신
- `SEPA_RUN_AFTER_CLOSE=0` — start_local 시 파이프라인 건너뜀
- `SEPA_BACKFILL_DAYS=84` — 백필 일수
- `SEPA_KILL_EXISTING_PORTS=1` — 기존 포트 점유 프로세스 종료
- `DART_API_KEY`, `FRED_API_KEY`, `ECOS_API_KEY` — Gamma 외부 데이터
