# 프로젝트 목적서 (한글)

작성일: 2026-03-09

## 1) 프로젝트 목적
본 프로젝트의 목적은 **OmX Multi-Agent 아키텍처**를 사용하여
Minervini SEPA 전략을 **설계 우선(Design First)** 방식으로 구현하고,
사장님의 EPC 엔지니어링 의사결정 체계를 금융 도메인으로 확장하는 것입니다.

핵심 산출물은 다음 3가지입니다.
1. 일일 종목 선별 결과(Alpha~Omega)
2. 재현 가능한 규칙 기반 의사결정 체인
3. 실전 배포 가능한 운영/검증/복구 표준

## 2) 현재 단계의 목표 (Execution Objective)
현재(2026-03-09) 목표는 다음과 같습니다.
- **Week 1 MVP:** Alpha 스크리너 실작동
- **동시 확장:** Beta(VCP) 자동 탐지 고도화
- **문서 고정:** 입력/출력 스키마, 운영 규약, 장애 복구 규칙 명문화

## 3) 성공 기준 (Done Definition)
- Alpha가 시장 유니버스에서 상위 후보를 일관되게 산출
- Beta가 Alpha 통과종목에서 VCP 신뢰도 점수 생성
- 결과 파일이 `.omx/artifacts/daily-signals/{YYYYMMDD}/`에 저장
- 오류/복구 이력이 `.omx/artifacts/audit-logs/`에 남음

## 4) 비즈니스 관점
- 단기: 내부 의사결정 자동화 (사장님 개인/팀 활용)
- 중기: 구독형 리포트 서비스(Freemium/Basic/Premium)
- 장기: B2B API(증권/운용사)로 확장

## 5) 원칙
1. Design First (설계 고정 후 구현)
2. Rule Integrity (미너비니 핵심 규칙 타협 금지)
3. Auditability (모든 의사결정 추적 가능)
4. Safe Execution (Paper Trading 기본)

## 6) 현재 구현 상태 업데이트 (2026-03-09)
- Live 수집 파이프라인 초안: `sepa/pipeline/refresh_market_data.py`
- 일일 사이클 실행기: `sepa/pipeline/run_live_cycle.py`
- Kiwoom 어댑터: `sepa/data/kiwoom.py` (엔드포인트 환경변수 주입형)
- 종목코드 변환 로직 추가: `.KS/.KQ -> 키움 코드` (`sepa/data/symbols.py`)
- 키움 엔드포인트 스펙 문서화: `docs/specs/KIWOOM_ENDPOINT_SPEC.md`
- Kiwoom 어댑터 강화: 다중 응답포맷 파싱 + 재시도/백오프 + audit 로그
- `SEPA_LIVE_MODE=1` 시 `run_mvp`가 refresh를 선행 실행하도록 통합
- Beta 점수식 보정: 수축비/거래량 기준 강화, 노이즈 패턴 제외 규칙 추가
- 백엔드 API 추가: `sepa/api/app.py` (FastAPI)
- 프론트 대시보드 추가: `sepa/frontend/*` (정적 HTML/JS)
- 실행 가이드: `docs/FRONTEND_BACKEND_RUNBOOK_KO.md`
