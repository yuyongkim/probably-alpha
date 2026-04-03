# Kiwoom REST Endpoint Spec (Draft)

Date: 2026-03-09

## 1) Env Variables
- `KIWOOM_TOKEN_URL`: OAuth token endpoint
- `KIWOOM_OHLCV_URL`: Daily OHLCV endpoint
- `KIWOOM_APP_KEY`
- `KIWOOM_SECRET_KEY`
- `KIWOOM_MARKET_TYPE` (KOSPI/KOSDAQ)
- `KIWOOM_QUERY_DATE` (YYYYMMDD, optional)

## 2) Token Request
- Method: `POST`
- Headers: `Content-Type: application/json`
- Body:
```json
{
  "grant_type": "client_credentials",
  "appkey": "...",
  "appsecret": "..."
}
```
- Response (expected):
```json
{
  "access_token": "..."
}
```

## 3) OHLCV Request
- Method: `POST`
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer {access_token}`
- Body (draft):
```json
{
  "symbol": "005930",
  "market_type": "KOSPI",
  "query_date": "20260309",
  "limit": 320
}
```

## 4) OHLCV Response (supported shapes)
- A) `{ "data": [...] }`
- B) `{ "output": [...] }`
- C) `[ ... ]`

Supported row fields (any of):
- date: `date` | `stck_bsop_date` | `일자`
- close: `close` | `stck_clpr` | `종가`
- volume: `volume` | `acml_vol` | `거래량`
