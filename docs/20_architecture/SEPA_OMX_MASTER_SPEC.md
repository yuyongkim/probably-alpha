# OmX Multi-Agent SEPA 상세 명세서 (Design First)

- 작성일: 2026-03-09 (KST)
- 범위: Alpha/Beta/Gamma(화학특화 포함)/Delta/Omega
- 목표: Minervini SEPA 규칙을 타협 없이 자동화 가능한 데이터-의사결정 파이프라인으로 구현

---

## 0) 전반 실행계획 (Roadmap)

### Phase 0. 설계 고정 (D+0 ~ D+2)
1. 전략 표준 고정: Minervini 8조건, VCP 정의, 손절 7~8%
2. 데이터 계약 고정: 입력/출력 JSON 스키마, 경로, 캐시 TTL
3. 검증 규약 고정: 정적/무결성/스모크/복구 기준

### Phase 1. MVP (Week 1)
- Alpha 단독 배포: 전체 유니버스 -> 상위 50
- 산출물: `.omx/artifacts/daily-signals/{YYYYMMDD}/alpha-passed.json`

### Phase 2. 패턴 확장 (Week 2~3)
- Beta(VCP) 추가: Alpha 50 -> VCP 10~20

### Phase 3. 의사결정 체인 완성 (Week 4+)
- Gamma/Delta/Omega 추가, 최종 3종목 리포트 자동생성

---

## 1) 공통 아키텍처

### 1.1 에이전트 흐름
Alpha -> Beta -> Gamma(+Gamma-Chem) -> Delta -> Omega

### 1.2 표준 경로
- 입력 데이터: `.omx/artifacts/market-data/`
- 일일 결과: `.omx/artifacts/daily-signals/{YYYYMMDD}/`
- 감사 로그: `.omx/artifacts/audit-logs/`

### 1.3 캐시 TTL
- Alpha: 300초
- Beta: 1시간
- Gamma: 1일

---

## 2) 환경변수 계약 (QuantDB .env 키 참고)

> 보안 원칙: 실제 키 값 저장/공유 금지, **키 이름만 계약**

### 2.1 필수 API 키
- `KIWOOM_APP_KEY`
- `KIWOOM_SECRET_KEY`
- `DART_API_KEY`
- `FRED_API_KEY`
- `ECOS_API_KEY`
- `EIA_API_KEY` (에너지/화학 거시 보강)

### 2.2 운영/파이프라인
- `DB_PATH`, `DOCS_DIR`
- `API_HOST`, `API_PORT`, `FRONTEND_PORT`
- `KIWOOM_MARKET_TYPE`, `KIWOOM_QUERY_DATE`
- `PRICE_PERIOD`, `PRICE_INTERVAL`

### 2.3 선택(확장)
- `KOSIS_API_KEY`, `EXIM_API_KEY`
- `YAHOO_TICKERS`

---

## 3) 에이전트별 상세 명세 템플릿

아래 템플릿을 각 에이전트마다 동일하게 사용:

### [Template]
- Agent ID:
- 책임/목표:
- 입력 스키마:
- 출력 스키마:
- 핵심 규칙:
- 검증 규칙:
- 실패/복구:
- 성능 KPI:
- 감사로그:

---

## 4) 에이전트별 실행 명세

## 4.1 Alpha_Screener
- Agent ID: `alpha_screener`
- 책임/목표: Minervini Trend Template 8조건으로 유니버스 필터링
- 입력 스키마:
  - symbol, date, open, high, low, close, volume
  - SMA50/150/200 계산 가능 최소 이력
- 출력 스키마: `alpha-passed.json`
  - date, symbol, score, rs_percentile, checks{8조건 bool}, reason
- 핵심 규칙:
  1) SMA50 > SMA150 > SMA200
  2) close > SMA50
  3) close >= 52주 고점의 75%
  4) close >= 52주 저점의 130%
  5) RS 백분위 기준 이상
  6~8) 나머지 조건 플래그
- 검증 규칙: score 내림차순, NaN 금지, 거래정지/상폐 제외
- 실패/복구: 데이터 결측 시 제외 + 로그 기록
- 성능 KPI: 2,500종목 처리 10분 이내
- 감사로그: `audit-logs/alpha-{timestamp}.log`

## 4.2 Beta_Chartist
- Agent ID: `beta_chartist`
- 책임/목표: VCP 패턴 감지 및 신뢰도 점수화
- 입력: Alpha 통과 종목 OHLCV
- 출력: `beta-vcp-candidates.json`
  - symbol, waves, contraction_ratio, volume_dryup, confidence
- 핵심 규칙: 2~4파동, 파동별 변동성 축소, 조정 구간 거래량 감소
- 검증: confidence 0~10, 가짜 삼각수렴 제거
- 실패/복구: peak 파라미터 단계적 완화(2%->1%)
- KPI: Alpha 50종목 기준 2분 이내

## 4.3 Gamma_Researcher (+Gamma_Chem)
- Agent ID: `gamma_researcher`
- 책임/목표: 실적 가속/산업모멘텀 정성+정량 스코어링
- 입력: Beta 후보 + DART/FRED/ECOS/EIA
- 출력:
  - `gamma-insights.json`
  - `gamma-chem-insights.json`
- 핵심 규칙: 매출/이익 가속, 부채/ROE/PER 필터, 화학 업황(유가/PMI/CAPEX)
- 검증: 물리 범위 점검(성장률 과대치 차단)
- 실패/복구: API 타임아웃 시 전일 캐시 + 주석

## 4.4 Delta_RiskManager
- Agent ID: `delta_risk`
- 책임/목표: 포지션 사이징, 손절, 손익비 검증
- 입력: Gamma 통과 종목 + 계좌/리스크 한도
- 출력: `delta-risk-plan.json`
  - entry, stop, target, qty, rr_ratio
- 핵심 규칙: 손절 7~8%, R/R >= 1.5
- 검증: qty 정수, 음수 금지
- 실패/복구: stop 비정상 시 entry*0.92 강제

## 4.5 Omega_PM
- Agent ID: `omega_pm`
- 책임/목표: 최종 3종목 선정 + 리포트
- 입력: Delta 결과
- 출력:
  - `omega-final-picks.json`
  - `omega-report.html` (PDF 실패 시 대체)
- 핵심 규칙: 점수/분산/섹터편중 제한
- 검증: 결과 1~3종목, 파일 생성 성공
- 실패/복구: PDF 실패 시 HTML 대체 + 알림 로그

---

## 5) 검증/운영 표준

## 5.1 정적 검증
- Python 컴파일/린트
- JSON Schema 검증

## 5.2 데이터 무결성
- Alpha 정배열 조건 재검증
- Beta confidence 범위
- Delta R/R >= 1.5

## 5.3 스모크 테스트
- 더미 데이터 1회, 실데이터 1회
- Alpha->Omega end-to-end dry-run

## 5.4 장애 대응
- 3회 연속 실패 시 긴급 알림 이벤트 생성

---

## 6) 즉시 실행 우선순위
1. Week 1: Alpha MVP (필수)
2. Week 2~3: Beta VCP
3. Week 4+: Gamma/Delta/Omega



---

## 7) 문서 링크 (KR/EN)
- 목적서(국문): `docs/PROJECT_OBJECTIVE_KO.md`
- Objective(EN): `docs/PROJECT_OBJECTIVE_EN.md`

## 8) 구현 상태 (2026-03-09)
- Alpha: CSV 기반 Minervini 8조건 필터 구현 완료
- Beta: 스윙포인트/수축비/거래량 건조도 + fallback 변동성 축소 기반 VCP 감지 구현
- Gamma: MacroDataProvider(FRED 키 사용 가능) + 화학 가점 기반 gamma_score 구현
- Delta: gamma_score 기반 포지션 수량/목표가/손익비(최소 1.5) 규칙 반영
- Omega: 최종 선정 + `omega-report.html` 자동 생성 구현
