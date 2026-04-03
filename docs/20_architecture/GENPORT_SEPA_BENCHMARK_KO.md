# GenPort Benchmark To SEPA

작성일: 2026-03-11

## 1. 벤치마크 핵심

`https://genport.newsystock.com/Main.aspx` 메인 페이지는 크게 아래 흐름으로 읽힌다.

1. 상단 글로벌 메뉴로 기능군을 먼저 분리한다.
2. 메인 본문은 단계형 체험 흐름으로 진입을 유도한다.
3. 결과 KPI와 큐레이션 모듈로 관심을 유지한다.
4. 교육, 지원, 운영 메뉴는 별도 축으로 분리한다.

SEPA에는 이 구조를 그대로 복제하지 않고 아래처럼 재해석한다.

1. 전략 체험 위저드 대신 `리더 탐색 -> 섹터 검증 -> 차트 검증 -> 실행 검토`
2. KPI는 마케팅용 수익률보다 `리더 수, 섹터 수, Alpha/Beta, Omega`
3. 큐레이션 섹션은 `추천, 백테스트, 히스토리`
4. 교육/참고 페이지는 메인 흐름 밖의 보조 허브로 유지

## 2. SEPA 정보구조 매핑

- GenPort `종목발굴/대시보드` -> SEPA `Command Center`
- GenPort `전략 생성 흐름` -> SEPA `Leader Pipeline`
- GenPort `성과/검증` -> SEPA `Chart Desk`, `Backtest Explorer`
- GenPort `포트 운영` -> SEPA `Recommendations`, `Omega Execution Plan`
- GenPort `아카데미` -> SEPA `Playbook Terms`, `Wizard Index`, `Strategy Frames`, `Korea Presets`

## 3. 병렬 작업 스트림

아래 4개는 병렬로 진행 가능하다.

1. 랜딩/정보구조
   `sepa/frontend/index.html`, `sepa/frontend/styles.css`
   상단 흐름, 섹션 순서, 앵커, CTA, 카드 레이아웃

2. 대시보드 렌더링 보강
   `sepa/frontend/js/main.js`
   `sepa/frontend/js/renderers/dashboard.js`
   섹션별 보조 메타, 요약 카피, 정렬 보조 로직

3. 실행/검증 화면 고도화
   `sepa/frontend/js/renderers/backtest.js`
   `sepa/frontend/js/renderers/recommendations.js`
   백테스트/추천 패널 밀도 조정, 비교 요약 강화

4. 참고 페이지 재정렬
   `sepa/frontend/glossary.html`
   `sepa/frontend/market-wizards.html`
   `sepa/frontend/market-wizards-people.html`
   `sepa/frontend/market-wizards-korea.html`
   메뉴 체계 통일, 카피 정리, 허브 연결 강화

## 4. 이번 1차 정리 범위

- 메인 대시보드를 `4단계 흐름형`으로 재배열
- 상단 내비게이션을 SEPA 중심 명칭으로 통일
- 참고 페이지 라벨을 새 정보구조에 맞춰 정리
- 기존 API 바인딩용 DOM ID는 최대한 유지

## 5. 다음 우선순위

1. `Recommendations`와 `Backtest Explorer` 상단에 비교형 요약 카드를 추가
2. `Chart Desk`에서 선택 종목 컨텍스트를 더 강하게 표시
3. `Command Center` 첫 화면에 실제 수치 기반 요약 배너를 추가
4. 필요하면 참고 페이지를 별도 허브 페이지로 묶기
