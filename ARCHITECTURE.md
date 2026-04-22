# ARCHITECTURE — ky-platform

> 통합 플랫폼의 데이터 흐름 · 6 탭 맵 · 멀티테넌시 · 시크릿 정책.

---

## 1. 데이터 흐름 (상위 → 하위)

```
 외부 소스
  ├─ KIS (한국투자증권 공식 API)
  ├─ Kiwoom (주가/거래량)
  ├─ DART (공시/재무)
  ├─ FRED · ECOS · KOSIS · EIA · EXIM (거시)
  └─ Naver (재무 보조, Kiwoom에 재무 없음)
        │
        ▼
 packages/adapters/        ← race/retry/timeout 통일, source 메타 기록
        │
        ▼
 packages/core/            ← PIT 재무·가격 저장소, 팩터 라이브러리 (QuantDB 승격 예정)
        │
        ▼
 apps/api/services/        ← 도메인 로직 (섹터강도, 리더점수, DCF, 백테스트 엔진)
        │
        ▼
 apps/api/routers/<tab>/   ← /api/v1/<tab>/... 얇은 어댑터
        │
        ▼
 apps/web/hooks/           ← React Query / SWR 페처
        │
        ▼
 apps/web/components/      ← shared + feature
        │
        ▼
 apps/web/app/<tab>/...    ← 페이지는 조립만 (100줄 이하)
```

---

## 2. 6 탭 × 서브섹션 맵

### 2.1 Chartist — 오늘의 시장
- `today` — 시장 요약, Top 섹터, Top 리더, 경고/알림
- `sectors` — 섹터 로테이션 히트맵, 강도 스코어보드
- `leaders` — 리더 스캔 결과 (Alpha → Beta → Gamma → Delta → Omega)
- `wizards/{alpha|beta|gamma|delta|omega|sigma}` — 단일 `<WizardPage/>` 재사용
- `watchlist` — 개인 관심종목
- `alerts` — 조건식 알림 설정

### 2.2 Quant — 팩터·백테스트
- `factors` — 팩터 유니버스, IC/IR, 턴오버
- `backtests/{list|run|detail}` — BT 실행/기록/상세
- `research` — 아이디어 노트북, 노트
- `portfolios` — 시뮬레이션 포트폴리오

### 2.3 Value — DCF·재무·RAG
- `dcf` — DCF 계산기 (Finance_analysis 포팅)
- `financials` — PIT 재무제표 뷰어
- `rag` — 버핏 Q&A (QuantPlatform 포팅)
- `screens` — 가치 스크리너 (P/B, EV/EBITDA, FCF yield)

### 2.4 Execute — 포지션·주문
- `overview` — 계좌 요약, 총손익
- `orders` — 주문 장부 (KIS)
- `positions` — 현재 포지션
- `risk-guard` — Delta 규칙 검증, 손절/목표가 설정

### 2.5 Research — 논문·거시
- `papers` — 논문 인덱스 (Dart_Analysis PDF 분석 포팅)
- `reports` — 리포트 아카이브
- `macro` — 매크로 지표 대시보드 (FRED/ECOS/KOSIS)
- `news` — 뉴스 피드

### 2.6 Admin — 운영
- `status` — 서비스 상태, 토큰 유효기간
- `jobs` — EOD 파이프라인 잡 기록
- `audit` — 데이터 이상치 로그
- `secrets` — shared.env 로드 상태 (값은 절대 노출 X)

**합계**: 6 탭 × 평균 6-10 서브섹션 ≈ **~50 라우트** (mockup 118 서브섹션 중 우선순위 순으로 Phase 3+ 에서 확장).

---

## 3. 멀티테넌시 준비

현재 단일 운영자(self) 기준, 그러나 미래 확장을 위해 **owner_id 를 모든 레이어에 삽입**.

### 3.1 규칙
- 모든 DB 스키마: `owner_id TEXT NOT NULL DEFAULT 'self'`
- 모든 API 라우트: `/api/v1/...` 버전 prefix
- 모든 서비스 함수: 첫 인자 또는 context 에 `owner_id` 전달
- 프론트 hooks: `useCurrentOwner()` 가 현재는 항상 `'self'` 반환

### 3.2 마이그레이션 경로
- Phase 3: owner_id 필드 삽입, 항상 `'self'` 사용
- Phase 5+: 실제 멀티테넌트로 확장 시 — auth 레이어 + row-level security

---

## 4. 시크릿 정책

### 4.1 3계층
1. **`~/.ky-platform/shared.env`** — 개인 공용 시크릿 (KIS, Kiwoom, DART, FRED, ECOS, KOSIS, Naver ...)
   - 모든 dev 스크립트가 **가장 먼저** 로드
   - 절대 레포에 포함 X
2. **`apps/api/.env`** — 로컬 오버라이드 (포트, 플래그 등만)
3. **환경 변수** — CI/CD / 배포 시 직접 주입

### 4.2 로드 순서 (scripts/dev.*)
```
shared.env  →  apps/api/.env  →  실행 셸의 env
(뒤로 갈수록 우선순위 높음)
```

### 4.3 금지
- `.env` 커밋
- 코드에 API 키 하드코딩
- 로그에 secret 출력 (printenv 계열 엔드포인트 금지)

---

## 5. 레거시 포팅 우선순위

| 레거시 | 승격 대상 | 우선순위 |
|---|---|---|
| QuantDB (mvp_platform) | `packages/core/` | **P0** |
| Company_Credit (Chartist 일부) | `apps/api/routers/chartist/` | P1 (운영 중 → 안전하게 병렬 운영) |
| QuantPlatform (PIT, RAG) | `packages/core/` + `apps/api/routers/value/` | P1 |
| Finance_analysis (DCF) | `apps/api/routers/value/` | P2 |
| Dart_Analysis (PDF) | `apps/api/routers/research/` | P2 |
| 한국투자증권 (KIS 샘플) | `packages/adapters/kis/` | P0 (execute 의존) |

---

## 6. 배포 & 운영

- 로컬 개발: `scripts/dev.sh` (api 8300 + web 8380)
- 레거시 `sepa.yule.pics` (port 8200) 는 병렬 운영 — 안정화 이전까지 건드리지 않음
- 배포 전략: Phase 5+ 에서 `/setup-deploy` 로 결정
