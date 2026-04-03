# api-contracts.md
> Backend API ↔ Frontend, 그리고 외부 소비자(B2B/API)와의 계약.

---

## 1. 공통 규칙

- 모든 API는 JSON 반환.
- snake_case 사용.
- 버전은 URL에 포함: `/api/v1/...`
- 응답은 최소한 다음 필드를 포함:

```json
{
  "ok": true,
  "data": "...",
  "error": null
}
```

에러 시:

```json
{
  "ok": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Backtest result not found",
    "detail": {}
  }
}
```

---

## 2. 주요 엔드포인트 계약

### 2.1 오늘 요약 (Summary)

- `GET /api/v1/summary`

```json
{
  "ok": true,
  "data": {
    "date": "20260403",
    "top_sectors": [
      {
        "sector_code": "SEC001",
        "sector_name": "반도체",
        "sector_score": 0.87
      }
    ],
    "top_leaders": [
      {
        "symbol": "005930",
        "name": "삼성전자",
        "leader_score": 0.81,
        "sector": "반도체"
      }
    ],
    "last_backtest": {
      "run_id": "bt_20260402_210000",
      "cagr": 0.234,
      "max_drawdown": -0.19
    }
  },
  "error": null
}
```

### 2.2 섹터/리더 목록

- `GET /api/v1/leaders/sectors`
- `GET /api/v1/leaders/stocks`

각각 `leader-sectors.json`, `leader-stocks.json` 스키마 그대로 노출.

### 2.3 백테스트 실행

- `POST /api/v1/backtest/run`

요청:

```json
{
  "strategy": "LeaderSectorStock_v1",
  "start": "20230101",
  "end": "20260403",
  "params": {
    "top_sectors": 5,
    "top_stocks_per_sector": 3,
    "rebalance": "weekly"
  }
}
```

응답:

```json
{
  "ok": true,
  "data": {
    "run_id": "bt_20260403_143022",
    "status": "QUEUED"
  },
  "error": null
}
```

---

## 3. 안정성 규칙

- 스키마 변경 시에는 반드시:
  - `schema_version` 증가
  - 기존 필드 삭제는 메이저 버전 업에서만
- 필수 필드는 절대 NULL/누락 허용하지 않음
