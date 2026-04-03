# UI_INFORMATION_ARCHITECTURE.md
> SEPA 주도주/주도섹터 대시보드 정보 구조 정의.
> "어떤 순서로 무엇을 보여줄 것인가"에 대한 설계 문서.

---

## 1. 타겟 사용자 & 주요 질문

### 1.1 타겟 사용자

- 나(개발자이자 트레이더)
- 추후: 한국 주식 성장주/주도주 전략에 관심 있는 개인/소규모 운용사

### 1.2 주요 질문

사용자가 대시보드를 열었을 때, 5~10초 안에 다음을 답할 수 있어야 한다.

1. 오늘 시장에서 **어떤 섹터가 가장 강한가?**
2. 그 섹터 안에서 **어떤 종목이 리더인가?**
3. 지금 당장 **매수 검토할 종목이 있는가?** (추천 + 리스크 플랜)
4. 최근 전략 성과는 어떤가? (백테스트 하이라이트)

---

## 2. 페이지 구조

### 2.1 Command Center (`index.html`) — 메인 대시보드

4단계 워크플로우로 구성:

| Stage | 이름 | 목적 | 데이터 소스 |
|-------|------|------|------------|
| 1 | **Leader Pipeline** | 확정 주도섹터/주도주 확인 | `/api/dashboard`, `/api/leaders/sectors`, `/api/leaders/stocks` |
| 2 | **Sector Lab** | 섹터 멤버십, 지속성, 점수 공식 드릴다운 | `/api/sector-members`, `/api/logic/scoring`, `/api/persistence` |
| 3 | **Chart Desk** | 개별 종목 차트/지표/EPS 검증 | `/api/stock/{symbol}/analysis` |
| 4 | **Validation & Execution** | 백테스트 + 추천 리뷰 + Omega 실행 플랜 | `/api/backtest/leaders`, `/api/recommendations/history`, `/api/omega` |

### 2.2 보조 페이지

| 페이지 | 파일 | 목적 | 데이터 소스 |
|--------|------|------|------------|
| Playbook Terms | `glossary.html` | 용어 정의 레퍼런스 | `/api/glossary` |
| Wizard Index | `market-wizards-people.html` | 73명 트레이더 프로필 인덱스 | 정적/내장 |
| Strategy Frames | `market-wizards.html` | 전략 철학 프레임워크 | 정적/내장 |
| Korea Presets | `market-wizards-korea.html` | 한국 시장 프리셋, 섹터 그룹, 백테스트 | `/api/leaders/sectors-grouped`, `/api/backtest/leaders`, `/api/catalog` |
| Wizard Screener | `wizard-screener.html` | 26개 전략 멀티 스크리너 | `/api/wizards/strategies`, `/api/wizards/screen` |
| Trader Debate | `trader-debate.html` | 가상 트레이더 토론 | `/api/trader-debate`, `/api/leaders/sectors` |

---

## 3. 네비게이션

```
Command Center (index.html)
├── Playbook Terms (glossary.html)
├── Wizard Index (market-wizards-people.html)
├── Strategy Frames (market-wizards.html)
├── Korea Presets (market-wizards-korea.html)
├── Wizard Screener (wizard-screener.html)
└── Trader Debate (trader-debate.html)
```

- 상단 네비게이션 바: 모든 페이지 간 이동
- 언어 전환: KO/EN 토글
- API Base URL: 사용자 입력 가능 (기본 `http://127.0.0.1:8000`)

---

## 4. Command Center 상세 레이아웃

### Stage 1: Leader Pipeline

```
┌─────────────────────────────────────────────┐
│ Confirmed Leaders        Near-Ready Queue   │
│ ┌──────────────────┐   ┌──────────────────┐ │
│ │ 주도 섹터 Top 5  │   │ 셋업 준비 종목   │ │
│ │ (점수+스파크)     │   │ (VCP 수축 진행)  │ │
│ ├──────────────────┤   ├──────────────────┤ │
│ │ 주도주 Top 10    │   │ 오늘 브리핑      │ │
│ │ (TT+RS+이유)     │   │                  │ │
│ └──────────────────┘   └──────────────────┘ │
└─────────────────────────────────────────────┘
```

### Stage 2: Sector Lab

```
┌─────────────────────────────────��───────────┐
│ 섹터 멤버십          스코어링 로직          │
│ ┌──────────────────┐ ┌────────────────────┐ │
│ │ 섹터 내 종목     │ │ 점수 공식 분해     │ │
│ │ + 기여도 표시    │ │ + 팩터별 가중치    │ │
│ ├──────────────────┤ ├────────────────────┤ │
│ │ 지속성 분석      │ │ Lookback/Forward   │ │
│ │ (과거 N일 유지)  │ │ 퍼시스턴스 차트    │ │
│ └──────────────────┘ └────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Stage 3: Chart Desk

```
┌─────────────────────────────────────────────┐
│ 가격 + 이동평균 차트                         │
│ 거래량 차트                                  │
│ RS 차트 (vs KOSPI)                           │
│ MACD 차트                                    │
│ EPS/실적 바 차트                             │
│ ┌─────────────────────────────────────────┐ │
│ │ TT 8조건 체크 / VCP 상태 / 선정 사유    │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Stage 4: Validation & Execution

```
┌─────────────────────────────────────────────┐
│ 백테스트 버킷        추천 히스토리           │
│ ┌──────────────────┐ ┌────────────────────┐ │
│ │ 주간/일간 성과   │ │ 최근 60일 추천     │ │
│ │ CAGR/Sharpe/MDD  │ │ 적중률/성과 추적   │ │
│ ├──────────────────┤ ├────────────────────┤ │
│ │ Omega 실행 플랜  │ │ 오늘 추천 TOP 3   │ │
│ │ Entry/Stop/Target│ │ + 사유 + R/R       │ │
│ └──────────────────┘ └────────────────────┘ │
└─────────────────────────────────────────────┘
```

---

## 5. JS 렌더러 매핑

| 렌더러 | 파일 | 담당 영역 |
|--------|------|----------|
| Dashboard | `js/renderers/dashboard.js` | Stage 1 리더 파이프라인 + 섹터 드릴다운 |
| Sector Grouped | `js/renderers/sector-grouped.js` | 섹터 그룹 스파크라인 카드 |
| Analysis | `js/renderers/analysis.js` | Stage 3 차트 데스크 |
| Stock Profile | `js/renderers/stock-profile.js` | 종목 프로필 다이얼로그, MA/EPS 차트 |
| Backtest | `js/renderers/backtest.js` | Stage 4 백테스트 버킷 |
| Recommendations | `js/renderers/recommendations.js` | Stage 4 추천 테이블 |
| Pagination | `js/renderers/pagination.js` | 페이지네이션 상태 관리 |
| Shared | `js/renderers/shared.js` | 공통 유틸 (포맷, 레이아웃) |

---

## 6. 인터랙션 패턴

### 6.1 종목 클릭 플로우

1. 주도주 테이블에서 종목 클릭
2. → Stock Profile 다이얼로그 오픈
3. → 차트 + TT 체크 + 선정 사유 한 화면에 표시
4. → "Chart Desk에서 분석" 버튼 → Stage 3로 스크롤

### 6.2 섹터 클릭 플로우

1. 주도 섹터 클릭
2. → Sector Lab (Stage 2) 섹터 멤버십 로드
3. → 해당 섹터 내 종목 리스트 + 기여도

---

## 7. 데이터 갱신 정책

- 대시보드 로드 시 1회 전체 API 호출
- 자동 폴링 없음 (수동 Refresh 버튼)
- `stale_data: true` 시 상단 경고 배너 표시
- 같은 세션 내 동일 요청은 메모리 캐시 재사용

---

## 8. 에러/빈 상태 처리

- API 실패:
  - "데이터를 불러오지 못했습니다" 메시지 + 재시도 버튼
  - 각 Stage가 독립적으로 실패 → 다른 Stage에 영향 없음
- Empty 상태:
  - 해당 날짜에 데이터가 없을 경우 친절한 메시지 + 다른 날짜 선택 안내
