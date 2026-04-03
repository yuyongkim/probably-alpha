# REPORTING_SCHEMA_SPEC.md
> 백테스트/포트폴리오 관련 엔티티의 JSON/DB 스키마 정의.
> 날짜는 항상 ISO 8601 형식(YYYY-MM-DD 또는 YYYY-MM-DDTHH:MM:SS+09:00).
> 금액/수량은 기본적으로 **원 단위, 주 단위** 사용.
> JSON 스키마와 DB 테이블 구조가 최대한 1:1로 매핑되게 설계한다.

---

## 1. 설계 원칙

- 날짜는 항상 ISO 8601 형식.
- 금액/수량은 기본적으로 **원 단위(정수), 주 단위** 사용.
- JSON 스키마와 DB 테이블 구조가 최대한 1:1로 매핑되게 설계한다.

---

## 2. 엔티티 목록

1. `strategy`
2. `portfolio`
3. `backtest_run`
4. `backtest_trade`
5. `backtest_order` (필요 시)
6. `backtest_equity_curve`
7. `backtest_period_return` (월/분기/연)

---

## 3. strategy

```json
{
  "id": "strat_sepa_leader_kosdaq_v1",
  "name": "SEPA Leader KOSDAQ v1",
  "description": "KOSDAQ 기준 SEPA 주도주 전략",
  "family": "GrowthMomentum",
  "created_at": "2026-04-03T12:00:00",
  "updated_at": "2026-04-03T12:00:00",
  "params": {
    "universe": "KOSDAQ",
    "min_market_cap": 30000000000,
    "min_avg_turnover_20d": 500000000,
    "rebalance_frequency": "weekly",
    "risk_per_trade": 0.01
  }
}
```

---

## 4. portfolio

```json
{
  "id": "port_sepa_kq_1",
  "name": "SEPA-KQ-1억-주간",
  "strategy_id": "strat_sepa_leader_kosdaq_v1",
  "state": "BACKTESTED",
  "initial_capital": 100000000,
  "currency": "KRW",
  "created_at": "2026-04-03T12:30:00",
  "updated_at": "2026-04-03T13:00:00",
  "settings": {
    "rebalance_frequency": "weekly",
    "risk_limits": {
      "max_positions": 10,
      "max_sector_positions": 3,
      "max_loss_per_trade": 0.02
    }
  },
  "backtest_runs": ["bt_20260403_143022"]
}
```

---

## 5. backtest_run

```json
{
  "id": "bt_20260403_143022",
  "portfolio_id": "port_sepa_kq_1",
  "strategy_id": "strat_sepa_leader_kosdaq_v1",
  "start_date": "2021-01-01",
  "end_date": "2026-04-03",
  "created_at": "2026-04-03T14:30:22",
  "params": {
    "execution": "next_open",
    "commission": 0.00015,
    "slippage": 0.001,
    "tax": 0.0018,
    "rebalance_frequency": "weekly"
  },
  "metrics": {
    "cagr": 0.182,
    "total_return": 0.812,
    "max_drawdown": -0.225,
    "sharpe": 1.12,
    "sortino": 1.45,
    "win_rate": 0.58,
    "profit_factor": 1.75,
    "trades": 320
  },
  "benchmark": {
    "symbol": "KOSDAQ",
    "cagr": 0.054,
    "total_return": 0.298,
    "max_drawdown": -0.37
  },
  "notes": {
    "lookahead_check": "PASSED",
    "survivorship_bias": "KRX 상폐종목 포함",
    "comment": "Gamma 실적 프록시 일부 사용"
  }
}
```

---

## 6. backtest_trade

```json
{
  "id": "tr_20240215_1",
  "run_id": "bt_20260403_143022",
  "portfolio_id": "port_sepa_kq_1",
  "symbol": "123456",
  "name": "예시전자",
  "side": "LONG",
  "entry_date": "2024-02-15",
  "exit_date": "2024-03-10",
  "entry_price": 50000,
  "exit_price": 57000,
  "quantity": 200,
  "gross_profit": 1400000,
  "net_profit": 1320000,
  "max_drawdown_pct": -0.08,
  "max_runup_pct": 0.20,
  "holding_period_days": 24,
  "reason_entry": "LeaderScore 상위 + VCP 수축",
  "reason_exit": "목표가 도달",
  "fees": {
    "commission_buy": 1500,
    "commission_sell": 1500,
    "slippage_cost": 8000,
    "tax": 20520
  }
}
```

---

## 7. backtest_equity_curve

```json
{
  "run_id": "bt_20260403_143022",
  "portfolio_id": "port_sepa_kq_1",
  "points": [
    {
      "date": "2021-01-04",
      "equity": 100000000,
      "benchmark": 100000000,
      "drawdown": 0.0
    },
    {
      "date": "2021-01-05",
      "equity": 100800000,
      "benchmark": 100200000,
      "drawdown": -0.01
    }
  ]
}
```

---

## 8. backtest_period_return (월별/연도별)

```json
{
  "run_id": "bt_20260403_143022",
  "portfolio_id": "port_sepa_kq_1",
  "frequency": "monthly",
  "rows": [
    {
      "period": "2024-01",
      "return": 0.045,
      "benchmark_return": 0.012,
      "trades": 14
    },
    {
      "period": "2024-02",
      "return": -0.012,
      "benchmark_return": -0.025,
      "trades": 10
    }
  ]
}
```
