# API_PRODUCT_PLAN.md
> 전략/데이터를 외부에 제공하는 API 제품 구상.
> 초기에는 내부/프론트엔드용, 이후 B2B 요금제 확장.

---

## 1. 제품 비전

- "한국 주식 주도 섹터/주도주 시그널 API"
- 타겟:
  - 개인/소규모 운용사, 퀀트 개발자, 트레이딩 봇 개발자
- 제공 가치:
  - 장 종료 기준 **주도 섹터/주도주** 시그널
  - 전략에 기반한 **백테스트/성능 시그널**
  - 백테스트 엔진과 함께 **검증 가능한 전략 레이어** 제공

---

## 2. API 레이어링

1. **Core Signals API**
   - `/leaders/sectors`
   - `/leaders/stocks`
   - `/sepa/alpha`, `/sepa/recommendations`
2. **Backtest API**
   - `/backtest/run`
   - `/backtest/result/{run_id}`
3. **Metadata & Health**
   - `/summary`
   - `/meta/schema`
   - `/health`

---

## 3. 초기 스코프 (v1)

### 3.1 Core Signals

- `GET /api/v1/leaders/sectors`
  - 오늘 또는 특정 날짜 기준 주도 섹터 Top N
  - 파라미터:
    - `date` (선택, 기본=오늘)
    - `limit` (기본=5)

- `GET /api/v1/leaders/stocks`
  - 섹터 필터 가능
  - 파라미터:
    - `date`
    - `sector_code` (선택)
    - `limit`

- `GET /api/v1/sepa/recommendations`
  - Omega 최종 추천 (1~3 종목)
  - 파라미터:
    - `date`

### 3.2 Backtest

- `POST /api/v1/backtest/run`
  - 전략 이름, 기간, 일부 파라미터를 받아 비동기로 실행
- `GET /api/v1/backtest/result/{run_id}`
  - JSON 성과 결과 반환

---

## 4. 현재 구현된 엔드포인트 (Phase 1 내부용)

### 4.1 데이터 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /api/health` | 헬스체크 |
| `GET /api/dashboard` | 전체 대시보드 페이로드 |
| `GET /api/latest` | 최근 세션 메타데이터 |
| `GET /api/summary` | 요약 통계 |
| `GET /api/leaders/sectors` | 확정 주도 섹터 |
| `GET /api/leaders/stocks` | 확정 주도주 |
| `GET /api/leaders/sectors-grouped` | 섹터별 그룹 + 스파크라인 |

### 4.2 시그널 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /api/alpha` | Alpha 통과 종목 |
| `GET /api/beta` | Beta VCP 후보 |
| `GET /api/gamma` | Gamma 인사이트 |
| `GET /api/delta` | Delta 리스크 플랜 |
| `GET /api/omega` | Omega 실행 플랜 (entry/stop/target/qty/R:R) |

### 4.3 종목 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /api/stock/{symbol}/profile` | 기업 프로필 (사업 요약, 재무, 체크) |
| `GET /api/stock/{symbol}/analysis` | 가격/거래량/MACD/RS/EPS 분석 |
| `GET /api/stock/{symbol}/overview` | 개요 (detail=true 옵션) |

### 4.4 추천/브리핑 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /api/recommendations` | 전체 추천 |
| `GET /api/recommendations/latest` | 최신 추천 |
| `GET /api/recommendations/history` | 히스토리 (기본 60일) |
| `GET /api/briefing` | 일일 브리핑 |
| `GET /api/briefing/latest` | 최신 브리핑 |

### 4.5 백테스트/분석 엔드포인트

| 경로 | 설명 |
|------|------|
| `GET /api/backtest/leaders` | 백테스트 버킷 탐색기 (period, buckets, sector_limit) |
| `GET /api/logic/scoring` | 스코어링 공식 + 산출 예시 |
| `GET /api/sector-members` | 섹터 멤버십 + 랭킹 근거 |
| `GET /api/persistence` | Lookback/Forward 지속성 분석 |

### 4.6 메타/유틸

| 경로 | 설명 |
|------|------|
| `GET /api/glossary` | 용어 정의 |
| `GET /api/catalog` | 유니버스 카탈로그 |
| `GET /api/snapshots/{date_dir}` | 과거 스냅샷 |
| `GET /api/wizards/strategies` | 위자드 전략 목록 (26개) |
| `GET /api/wizards/screen` | 위자드 스크리닝 결과 |
| `GET /api/trader-debate` | 트레이더 토론 랭킹 |

### 4.7 Admin (토큰 보호)

| 경로 | 설명 |
|------|------|
| `POST /api/admin/daily-signals` | 지정 날짜 시그널 빌드 |
| `POST /api/admin/history/backfill` | 히스토리 백필 실행 |

---

## 5. 요금제/플랜 (초기 아이디어)

**v1에서는 내부용**으로만 사용하고, 상용화 시 다음과 같이 확장할 수 있다.

### 5.1 Tier 구상 (개념)

1. **Free / Dev**
   - 최근 5거래일 Signals 조회
   - 일일 호출 제한 낮게

2. **Pro**
   - 3개월~1년 Signals 조회
   - 단일 전략 Backtest 호출 제한 포함
   - 개인/소규모 팀

3. **Enterprise**
   - 전체 히스토리
   - 커스텀 전략 백테스트
   - 전용 서포트/SLAs

(실제 가격/조건은 나중에 별도 기획)

---

## 6. 보안/인증 (향후)

- API Key 기반 인증
  - `X-API-KEY` 헤더
- 속도 제한:
  - 기본 `N` calls/minute
- IP 제한/로그:
  - 요청 로그를 집계해 과도한 호출/이상 징후 탐지
- Admin 엔드포인트:
  - `SEPA_ADMIN_TOKEN` 환경변수 기반 토큰 보호 (현재 구현 완료)

---

## 7. 성공 지표 (제품 관점)

- (내부 단계)
  - 내가 직접 대시보드 + CLI + 노트북에서 잘 가져다 쓰고 있는지
  - 일일 파이프라인 안정성 (장애 없이 시그널 생성)
- (외부 단계 가정)
  - 활성 키 수
  - 월간 호출 수
  - API 기반으로 만들어진 자체 툴/전략 수

---

## 8. 향후 확장 아이디어

- REST + Webhook:
  - 장 종료 시점에 오늘 주도 섹터/주도주 리스트를 Webhook으로 푸시
- Bulk Export:
  - 전 기간 Signals/백테스트 결과를 파일로 내려주는 엔드포인트
- Custom Strategy:
  - 사용자가 파라미터로 커스터마이징한 전략을 제출하면 백테스트 후 결과 반환
- Streaming:
  - WebSocket 기반 실시간 시그널 업데이트 (장중 모니터링용)

---

## 9. v1 → v2 마이그레이션 가이드라인

- URL prefix `/api/v1/` → `/api/v2/`
- v1은 v2 출시 후 최소 6개월 유지
- Breaking change 시:
  - 메이저 버전 증가
  - 마이그레이션 가이드 별도 문서 작성
  - 클라이언트에 사전 고지 (최소 1개월)
