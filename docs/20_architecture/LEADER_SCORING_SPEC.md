# LEADER_SCORING_SPEC.md
> 주도 섹터 점수 및 주도주 점수 공식 정의.
> 공식 변경 시 `scoring/sector_strength.py`, `scoring/leader_stock.py`도 함께 업데이트.

---

## 1. 주도 섹터 점수 (Sector Strength Score)

### 목적
오늘 종가 기준으로 **지속성 있는 강세 섹터**를 탐지한다.
단순 1일 등락률이 아니라 **중기 모멘텀 + breadth(폭) + 거래대금 추세**를 결합한다.

### 점수 공식

```
SectorScore =
    0.30 * RS_20          (KOSPI/KOSDAQ 대비 20일 상대수익률 백분위)
  + 0.25 * RS_60          (60일 상대수익률 백분위)
  + 0.15 * Breadth_50MA   (섹터 내 50일선 위 종목 비율)
  + 0.15 * NearHighRatio  (52주 고점 80% 이상 종목 비율)
  + 0.15 * TurnoverTrend  (최근 20일 평균 거래대금 / 60일 평균 거래대금)
```

### 팩터 정의

| 팩터            | 계산 방식                                                         | 범위 |
|-----------------|-------------------------------------------------------------------|------|
| `RS_20`         | 섹터 20일 수익률 − 벤치마크 20일 수익률 → 전 섹터 기준 백분위      | 0~1  |
| `RS_60`         | 동일, 60일 기준                                                   | 0~1  |
| `Breadth_50MA`  | `close > MA50` 인 종목 수 / 섹터 전체 종목 수                     | 0~1  |
| `NearHighRatio` | `close >= 52주 고점 * 0.80` 인 종목 수 / 섹터 전체 종목 수        | 0~1  |
| `TurnoverTrend` | `mean(turnover_20d) / mean(turnover_60d)` → clip(0, 3) 후 0~3 사용 | 0~3  |

### 제외 조건

- 섹터 내 **거래 가능 종목 수 < 5** → 점수 계산 제외
- 섹터 전체 **거래대금 < 100억** → 유동성 부족으로 제외

### 출력 스키마: `leader-sectors.json`

```json
{
  "schema_version": "1.0",
  "date": "20260403",
  "generated_at": "2026-04-03T17:10:00",
  "pipeline_run_id": "run_20260403",
  "stale_data": false,
  "top_sectors": [
    {
      "sector_code": "SEC001",
      "sector_name": "반도체",
      "sector_score": 0.87,
      "rs_20": 0.91,
      "rs_60": 0.83,
      "breadth_50ma": 0.72,
      "near_high_ratio": 0.65,
      "turnover_trend": 1.23,
      "stock_count": 42
    }
  ]
}
```

---

## 2. 주도주 점수 (Leader Stock Score)

### 목적
주도 섹터 내에서 **오늘 진입을 검토할 수 있는 최선두 종목**을 찾는다.
Minervini Trend Template + RS + VCP 준비 상태를 결합한다.

### 점수 공식

```
LeaderScore =
    0.25 * RS_120              (120일 상대강도 백분위)
  + 0.20 * TrendTemplate       (TT 8조건 충족 비율, 0~1)
  + 0.15 * Near52WHigh         (52주 고점 근접도)
  + 0.15 * VolumeExpansion     (거래량 팽창도)
  + 0.15 * VolatilityContraction (변동성 수축도)
  + 0.10 * EarningsProxy       (실적/대체 지표)
```

### 팩터 정의

| 팩터                  | 계산 방식                                                        | 범위 |
|-----------------------|------------------------------------------------------------------|------|
| `RS_120`              | 120일 수익률 → 전 종목 대비 백분위                              | 0~1  |
| `TrendTemplate`       | Minervini 8조건 만족 개수 / 8                                   | 0~1  |
| `Near52WHigh`         | `close / rolling_max(close, 252)`                               | 0~1  |
| `VolumeExpansion`     | `mean(volume_5d) / mean(volume_50d)` → clip(0, 3) 후 /3로 정규화 | 0~1  |
| `VolatilityContraction` | `1 - (ATR_10 / ATR_50)` → clip(0, 1)                          | 0~1  |
| `EarningsProxy`       | DART EPS QoQ/YoY 기반 점수, 없으면 최근 거래대금 가속 등으로 대체 | 0~1  |

### 최소 자격 게이트 (Fail 시 점수 계산 대상에서 제외)

- `TrendTemplate < 5/8`  (8조건 중 절반 미만)
- `close < MA50`
- 시가총액 `< 300억`
- 최근 20일 평균 거래대금 `< 5억`
- 거래정지/관리종목/스팩/ETF/ETN

### 출력 스키마: `leader-stocks.json`

```json
{
  "schema_version": "1.0",
  "date": "20260403",
  "generated_at": "2026-04-03T17:10:05",
  "pipeline_run_id": "run_20260403",
  "stale_data": false,
  "leaders": [
    {
      "symbol": "005930",
      "name": "삼성전자",
      "sector": "반도체",
      "leader_score": 0.81,
      "rs_120_pct": 0.88,
      "trend_template_score": 0.875,
      "near_52w_high": 0.93,
      "volume_expansion": 1.45,
      "volatility_contraction": 0.62,
      "earnings_proxy": 0.70,
      "trend_checks": {
        "tt1_sma50_gt_150_200": true,
        "tt2_close_gt_sma50": true,
        "tt3_close_gte_75pct_52wh": true,
        "tt4_close_gte_130pct_52wl": true,
        "tt5_sma150_gt_sma200": true,
        "tt6_sma200_rising": true,
        "tt7_rs_gte_threshold": true,
        "tt8_close_gt_sma200": true
      },
      "reason": "RS상위+VCP수축진행+거래량건조"
    }
  ]
}
```
