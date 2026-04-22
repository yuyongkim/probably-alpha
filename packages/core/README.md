# packages/core

> **Status**: placeholder. QuantDB `mvp_platform` 를 여기로 승격 예정.

## 역할

데이터 코어. 모든 도메인 서비스가 의존하는 순수 데이터·계산 레이어.

- PIT (Point-in-Time) 재무 저장소
- 가격/거래량 시계열 (캐시 포함)
- 팩터 라이브러리 (모멘텀, 밸류, 퀄리티 ...)
- 유니버스 필터
- 날짜/영업일 유틸

## 원칙

- I/O 없음 — 외부 API 호출은 `packages/adapters/` 로 분리
- 결정적 함수 선호
- 모든 함수는 `owner_id` 맥락을 받도록 설계

## 승격 계획

1. `QuantDB/mvp_platform/` 의 코어 모듈을 `ky_core/` 로 이동
2. 테스트 함께 이동
3. `apps/api/services/` 가 이 패키지를 import 하도록 전환
4. 레거시 경로는 `legacy/quantdb/` README 로만 참조 유지
