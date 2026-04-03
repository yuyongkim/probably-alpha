# BACKTEST_RULES.md
> 백테스트 실행 원칙. 이 문서를 어기면 백테스트 결과는 신뢰 불가.

***

## 1. 절대 원칙 (위반 시 결과 무효)

### 1.1 Look-Ahead Bias 금지
- 신호는 **종가 확정 이후** 사용 가능한 데이터만 활용한다.
- 이동평균, RS, 볼린저밴드 등 모든 지표는 **당일 종가 기준**으로만 계산한다.
- 실적/DART 공시는 **발표일 +1 거래일** 이후부터 신호에 반영한다.
- 종가 기준 신호가 나왔는데, 같은 날 그 종가로 체결했다고 가정하는 것 금지(동일 캔들 체결 금지).

### 1.2 체결 가정 명시 (기본: next-open)
```python
# 옵션 A: same-close (권장 X)
# 현실: 장 마감 직전 시장가 → 슬리피지 과대
execution_price = close_price

# 옵션 B: next-open  [기본값]
execution_price = next_day_open

# 옵션 C: next-close
execution_price = next_day_close
```
- 기본값은 **next-open** 사용.
- 실행 옵션은 `backtest_result.json`의 `params.execution`에 기록.

### 1.3 Survivorship Bias 처리
- 백테스트 기간 내 **상장폐지/합병/거래정지 종목 포함** 필수.
- 상폐 시 마지막 거래일 종가로 강제 청산, 사유 기록.
- `survivorship_bias_note` 필드에 요약.

***

## 2. 비용 반영

```python
COMMISSION_RATE = 0.00015   # 0.015% (매수/매도 각각)
SLIPPAGE_RATE   = 0.001     # 0.1%
TAX_RATE        = 0.0018    # 증권거래세 0.18% (매도 시)

# 시가총액 < 500억: 슬리피지 x2.0
# 시가총액 < 1000억: 슬리피지 x1.5
# 20일 평균 거래대금 < 10억: 백테스트 대상 제외
```

- 총 왕복 비용 대략 **0.4% 수준**으로 설계 (현실 감안).

***

## 3. 리밸런싱 규칙

### 3.1 리밸런싱 빈도
- 기본: **주 1회 (매주 금요일 종가 기준)**
- 일간 리밸런싱은 탐색용(아이디어 확인), 성과 측정은 주간 이상.

### 3.2 포지션 청산 조건 (아래 중 하나라도 발생 시)
1. 종목 섹터가 **Top N 섹터**에서 이탈
2. 종목 `LeaderScore`가 전체의 **하위 20% 이하**
3. `close < MA50` (추세 이탈)
4. 손절: `entry 대비 -7~8%` 하락
5. 백테스트 기간 종료

### 3.3 진입 조건
- 리밸런싱일 기준 `LeaderScore` 상위 M (섹터별 Top 3 등)
- `LEADER_SCORING_SPEC.md`의 **게이트 조건 충족**
- 동일 섹터 **최대 2종목**

### 3.4 포지션 사이징
- 기본: **동일 가중(Equal Weight)**
- 변동성 조정 사이징은 옵션 플래그로 On/Off.

***

## 4. 성과 지표

필수로 계산하는 지표:

| 구분   | 지표            | 설명 |
|--------|-----------------|------|
| 수익성 | `CAGR`          | 연환산 복리 수익률 |
|        | `Total_Return`  | 전체 기간 수익률 |
|        | `Sharpe_Ratio`  | (연환산 수익률 − 무위험수익률) / 연환산 변동성 |
|        | `Sortino_Ratio` | 하방 변동성만 사용한 Sharpe |
| 리스크 | `Max_Drawdown`  | 최대 낙폭 |
|        | `MDD_Duration`  | 최대 낙폭 지속 일수 |
|        | `Volatility`    | 연환산 변동성 |
| 매매   | `Win_Rate`      | 수익 거래 비율 |
|        | `Profit_Factor` | 총 수익 / 총 손실 |
|        | `Annual_Turnover`| 연간 회전율 |
| 벤치   | `Alpha`         | 벤치마크 대비 초과 수익 |
|        | `Beta`          | 시장 민감도 |
|        | `Info_Ratio`    | 알파 / 추적 오차 |

***

## 5. 과최적화 방지

### 5.1 IS/OOS 분리
- In-Sample : Out-of-Sample = **7:3** 권장
- 파라미터 튜닝은 IS에서만, 평가/보고는 OOS 기준.

### 5.2 Walk-Forward 검증
- 기간을 여러 윈도우로 나눈 후:
  1. 각 윈도우에서 IS 튜닝
  2. 직후 OOS 검증
  3. OOS 구간들만 이어서 최종 성과 계산

### 5.3 다중 비교 편향
- 수백 조합 중 "제일 좋은 것"만 고르는 행위 금지.
- 결과 선택 기준(예: Sharpe 우선, 그 다음 MDD)을 **사전에 고정**.

***

## 6. 결과 저장 형식

`backtest_result.json` 예시:

```json
{
  "run_id": "bt_20260403_143022",
  "strategy": "LeaderSectorStock_v1",
  "period": {"start": "20230101", "end": "20260403"},
  "params": {
    "top_sectors": 5,
    "top_stocks_per_sector": 3,
    "rebalance": "weekly",
    "execution": "next-open",
    "commission": 0.00015,
    "slippage": 0.001
  },
  "metrics": {
    "cagr": 0.234,
    "total_return": 0.891,
    "sharpe": 1.42,
    "max_drawdown": -0.187,
    "win_rate": 0.58,
    "annual_turnover": 4.3
  },
  "benchmark": {
    "cagr": 0.088,
    "alpha": 0.146
  },
  "survivorship_bias_note": "상폐 종목 12건 포함, 마지막 거래일 청산 처리",
  "lookback_check": "PASSED",
  "schema_version": "1.0",
  "generated_at": "2026-04-03T14:30:22"
}
```
