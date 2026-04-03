# kiwoom-adapter-check.md
> 키움 API 어댑터/데이터 파이프라인 점검 스킬.
> Source of Truth는 `docs/30_data_contracts/KIWOOM_ENDPOINT_SPEC.md`.

---

## 1. 이 스킬을 언제 쓸 것인가

- "키움 API 연결 안 되는데 확인해줘"
- "시세 데이터가 안 들어오는데 뭐가 문제인지"
- "Kiwoom → Yahoo 폴백이 제대로 동작하는지 확인"
- "refresh_market_data.py 에러 디버깅"

---

## 2. 헬스체크 순서

### 2.1 환경변수 확인

- `.env` 파일에 다음이 설정되어 있는지:
  - `KIWOOM_APP_KEY`
  - `KIWOOM_SECRET_KEY`
  - `KIWOOM_MARKET_TYPE` (기본: `0,10,3`)

### 2.2 API 연결 테스트

```python
from sepa.data.kiwoom import KiwoomProvider
provider = KiwoomProvider()
print(provider.health())
```

- 정상: `{"status": "ok", ...}`
- 실패: 토큰 발급 에러, 네트워크 에러 등

### 2.3 데이터 소스 폴백 확인

```python
from sepa.data.quantdb import health as quantdb_health
print(quantdb_health())
```

- QuantDB SQLite 상태 확인
- Yahoo Finance 연결: `yfinance.download('005930.KS', period='5d')` 테스트

---

## 3. 폴백 순서 (data-integrity 규칙 준수)

1. **Kiwoom REST API** (정식 데이터 소스)
2. **QuantDB** (로컬 SQLite)
3. **Yahoo Finance** (`.KS`/`.KQ` 티커)
4. **전일 캐시** + `stale_data: true` 플래그
5. **샘플 데이터** (최후 수단, 실전 사용 금지)

---

## 4. 주요 에러 패턴 & 대응

| 증상 | 원인 | 조치 |
|------|------|------|
| 401 Unauthorized | 토큰 만료 또는 키 오류 | `.env` 키 값 확인, 토큰 재발급 |
| 빈 응답 (data=[]) | 비거래일, 정기점검, 종목코드 오류 | 날짜/종목코드 확인, Yahoo 폴백 |
| Rate limit (429) | 초당 5회 초과 | 호출 간격 0.25초 이상 확인 |
| 응답 파싱 실패 | 키움 응답 형식 변경 | `sepa/data/kiwoom.py` 다중 파서 확인 (data/output/배열 3형식) |
| 타임아웃 | 네트워크 불안정 | 재시도/백오프 로직 확인, audit-log 기록 |
| 종가 불일치 | 소스 간 데이터 차이 | 0.5% 이상 차이 시 불일치 마킹 (data-integrity 규칙) |

---

## 5. 관련 파일

- `sepa/data/kiwoom.py` — 어댑터 구현 (OAuth + OHLCV + 다중 파서)
- `sepa/pipeline/refresh_market_data.py` — 메인 오케스트레이터
- `sepa/data/quantdb.py` — QuantDB 로컬 SQLite
- `sepa/data/symbols.py` — 종목코드 변환 (`to_kiwoom_symbol`, `infer_market`)
- `docs/30_data_contracts/KIWOOM_ENDPOINT_SPEC.md` — API 스펙

---

## 6. 금지 사항

- API 수준의 병렬/과도한 호출을 제안하지 않는다.
- 데이터 품질 문제가 확실하지 않은데도 "문제 없다"고 단���하지 않는다.
- 반대로, 단순한 일시적 오류를 시스템 전체 문제로 과장하지 않는다.
