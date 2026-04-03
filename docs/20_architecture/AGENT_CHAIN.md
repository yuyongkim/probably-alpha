# AGENT_CHAIN.md
> Alpha → Beta → Gamma → Delta → Omega 에이전트 체인 흐름 및 입출력 연결 정의.
> 각 에이전트 상세 명세는 `SEPA_OMX_MASTER_SPEC.md` 참고.

***

## 전체 흐름

```
[market-data/*.csv]
        |
        v
[ Universe Filter ]
  sepa/data/universe.py
  - 거래정지/관리/ETF/스팩 제외
  - 시가총액 >= 300억
  - 20일 평균 거래대금 >= 5억
  → symbol list (~1800~2200)
        |
        +--------------------+
        v                    v
   [ ALPHA ]           [ LEADER SECTOR SCAN ]
   Trend Template      sector_strength.py
   8조건 필터          → leader-sectors.json (Top 5 섹터)
   ~50 통과                  |
        |                    v
        v             [ LEADER STOCK SCAN ]
   [ BETA ]           leader_stock.py
   VCP 패턴           → leader-stocks.json (섹터별 Top 3)
   ~10~20
        |
        v
   [ GAMMA (+Chem) ]
   실적 가속 + 매크로/화학
        |
        v
   [ DELTA ]
   포지션 사이징, 손절, 목표, 수량
        |
        v
   [ OMEGA ]
   최종 1~3 종목 + 리포트
```

***

## 에이전트별 입출력 계약

### Alpha

- 입력
  - `market-data/ohlcv/{SYMBOL}.csv`: OHLCV 일봉 (최소 252일)
- 출력
  - `daily-signals/{YYYYMMDD}/alpha-passed.json`
- 필드
  - `date`, `symbol`, `score`, `rs_percentile`, `checks`(TT 8조건 bool), `reason`
- 통과 기준
  - `TrendTemplate >= 5/8`
- 성능
  - 2500 종목 기준 10분 이내

### Beta

- 입력
  - `alpha-passed.json` + 해당 종목 OHLCV
- 출력
  - `beta-vcp-candidates.json`
- 필드
  - `symbol`, `waves`, `contraction_ratio`, `volume_dryup`, `confidence`(0~10)
- 성능
  - Alpha 50 종목 기준 2분 이내

### Gamma (+Gamma-Chem)

- 입력
  - `beta-vcp-candidates.json`
  - DART/FRED/ECOS/EIA 등 외부 데이터
- 출력
  - `gamma-insights.json`, `gamma-chem-insights.json`
- 필드
  - `symbol`, `eps_qoq`, `eps_yoy`, `revenue_growth`, `roe`,
    `macro_score`, `chem_score`, `gamma_score`
- 폴백
  - API 타임아웃 → 전일 캐시 + `stale_data: true`

### Delta

- 입력
  - `gamma-insights.json`
  - 계좌 리스크 한도(.env)
- 출력
  - `delta-risk-plan.json`
- 필드
  - `symbol`, `entry`, `stop`, `target`, `qty`, `rr_ratio`
- 하드 룰
  - `stop = entry * (1 - 0.07 ~ 0.08)`
  - `rr_ratio >= 1.5`

### Omega

- 입력
  - `delta-risk-plan.json`
- 출력
  - `omega-final-picks.json`, `omega-report.html` (또는 PDF 실패 시 HTML)
- 필드
  - `picks`(1~3), `rank`, `total_score`, `sector`,
    `entry`, `stop`, `target`, `reason`
- 실패 복구
  - PDF 실패 → HTML 생성 + `omega_fallback: true`

### Leader Sector Scan

- 입력
  - 전체 유니버스 OHLCV + 섹터 매핑
- 출력
  - `leader-sectors.json`
- 필드
  - `sector_code`, `sector_name`, `sector_score`,
    `rs_20`, `rs_60`, `breadth_50ma`, `near_high_ratio`,
    `turnover_trend`, `stock_count`

### Leader Stock Scan

- 입력
  - `leader-sectors.json` 기준 Top 5 섹터의 종목 OHLCV
- 출력
  - `leader-stocks.json`
- 필드
  - `symbol`, `name`, `sector`, `leader_score`,
    `rs_120_pct`, `trend_template_score`,
    `near_52w_high`, `volume_expansion`,
    `volatility_contraction`, `earnings_proxy`,
    `trend_checks`, `reason`

***

## 에러/복구 정책

| 에이전트 | 실패 조건           | 복구 동작                                   |
|---------|---------------------|---------------------------------------------|
| Alpha   | 데이터 결측         | 해당 종목 제외 + audit log 기록            |
| Alpha   | API 오류            | Yahoo 폴백 → 실패 시 전일 데이터 사용      |
| Beta    | peak 탐지 실패      | threshold 완화 (2% → 1%) 재시도            |
| Gamma   | API 타임아웃        | 전일 캐시 + `stale_data: true`             |
| Delta   | stop 비정상         | `entry * 0.92` 강제 + 경고 로그            |
| Omega   | PDF 생성 실패       | HTML 대체 + `omega_fallback: true`         |
| 전체    | 동일 에이전트 3회 실패 | 긴급 알림 이벤트 생성                    |
