# 데이터 소스 카탈로그 (Data Sources Catalog)

> 이 문서는 `~/.ky-platform/finance.ini`의 글로벌 데이터 소스 지형도를
> ky-platform 어댑터 현황과 매핑한 인덱스다.
> "한투 API 제약에서 벗어나 **실물경제 → 주가** 인과관계를 추적할 수 있는
> 글로벌 오픈 데이터 생태계 최대한 활용"이 목표.
>
> 어댑터는 `packages/adapters/ky_adapters/<source>/`에 산다.

---

## 현재 구현 상태 (2026-04-25, 갱신)

| Status | Adapter |
|---|---|
| **OK** 구현됨 (14개) | `kis` · `dart` · `ecos` · `kosis` · `fred` · `eia` · `exim` · `naver_fnguide` · **`customs`** · **`oecd`** · **`worldbank`** · **`pytrends`** · **`cftc`** · **`un_comtrade`** |
| **TODO 1순위** | `yfinance` · `pykrx` (정책 검토 필요 — KIS-only 정책과의 충돌 여부) |
| **TODO 2순위** | `imf` · `kita` · `ecb` · `bis` |
| **TODO 3순위** | `polygon` · `alpha_vantage` · `usda` |
| 보류 | LME · CME/CBOT · Investing.com (모두 크롤링/제한) · Bloomberg/Refinitiv (유료) |

### 2026-04-25 추가 어댑터 헬스체크 결과

| 어댑터 | 응답 시간 | 샘플 행 | 비고 |
|---|---|---|---|
| customs | 543ms | 668 | HS×국가 월별 endpoint 검증 완료. 나머지 5개 endpoint는 data.go.kr 활용신청 승인 대기 |
| oecd | 3.2s | 3 | 한국 CLI 시리즈 정상 |
| worldbank | 639ms | 5 | 한국 GDP 5년치 정상 |
| cftc | 1.1s | 5 | CRUDE OIL COT 검색 정상 |
| un_comtrade | 940ms | 0 | 응답 정상, 최신 6개월 lag 데이터는 미공개 (예상) |
| pytrends | 3.0s | 91 | 한국 검색어 '반도체' 3개월 정상 |

---

## 카테고리별 전체 지형도

### ① 주식·금융 시세

| Source | 커버리지 | API | 무료 | 특징 | 어댑터 |
|---|---|---|---|---|---|
| **yfinance** | 글로벌 | Python 라이브러리 | 완전무료 | 섹터 메타데이터 포함, 가장 범용적 | **TODO** `yfinance` |
| **pykrx** | 한국 전체 | Python 라이브러리 | 완전무료 | KRX 공식, 업종지수 강점 | **TODO** `pykrx` |
| **FinanceDataReader** | 한국+글로벌 | Python 라이브러리 | 완전무료 | 종목 리스트·인덱스 | **TODO** `fdr` (선택) |
| KIS | 한국 | REST + WS | 무료(인증) | 실시간 호가·체결 | **OK** `kis` |
| Naver/FnGuide | 한국 재무 | 크롤링 | 무료 | EPS·ROE·세그먼트 | **OK** `naver_fnguide` |
| Alpha Vantage | 미국+글로벌 | REST | 무료 티어 | 분당 5콜 제한 | TODO 3순위 |
| Polygon.io | 미국 | REST | 무료 티어 | 실시간 강점 | TODO 3순위 |

### ② 거시경제·매크로

| Source | 커버리지 | API | 무료 | 특징 | 어댑터 |
|---|---|---|---|---|---|
| **FRED** (Fed) | 미국+글로벌 | REST | 완전무료 | 800K+ 시리즈 | **OK** `fred` |
| **ECOS** (한은) | 한국 금융 | REST | 완전무료 | 금리·환율·BSI | **OK** `ecos` |
| **OECD** | 선진국 | REST (SDMX) | 완전무료 | **CLI 경기선행지수** | **TODO** `oecd` |
| **World Bank** | 전세계 | REST | 완전무료 | GDP·산업비중·장기 | **TODO** `worldbank` |
| IMF | 전세계 | REST (SDMX) | 완전무료 | 환율·외환보유액 | TODO 2순위 |
| ECB | 유럽 | REST (SDMX) | 완전무료 | 유로존 금리 | TODO 3순위 |
| BIS | 글로벌 금융 | REST | 완전무료 | 중앙은행 데이터 | TODO 3순위 |

### ③ 한국 통계·산업

| Source | 커버리지 | API | 무료 | 특징 | 어댑터 |
|---|---|---|---|---|---|
| **KOSIS** (통계청) | 한국 전체 | REST | 완전무료 | 산업생산·출하·재고 | **OK** `kosis` |
| **DART** (금감원) | 한국 상장사 | REST | 완전무료 | 재무제표·공시 | **OK** `dart` |
| **EXIM** (수출입은행) | 환율 | REST | 완전무료 | 일별 환율 | **OK** `exim` |
| **관세청 TRASS** | 한국 무역 | REST | 완전무료 | **HS코드별 수출입 실시간** — 화학섹터 핵심 | **TODO** `customs` |
| 산업통상자원부 | 한국 산업 | REST | 완전무료 | 에너지통계·산업정책 | TODO 보류 |
| KRX 정보데이터 | 한국 증시 | REST | 완전무료 | 업종지수·투자자동향 | (pykrx로 대체 가능) |

### ④ 원자재·에너지 (화학섹터 핵심)

| Source | 커버리지 | API | 무료 | 특징 | 어댑터 |
|---|---|---|---|---|---|
| **EIA** (US Energy) | 에너지 전체 | REST | 완전무료 | 유가·천연가스·정제가동률 | **OK** `eia` |
| USDA | 농산물 | REST | 완전무료 | 글로벌 농산물 수급 | TODO 3순위 |
| LME | 비철금속 | 제한적 | 일부 무료 | 구리·알루미늄 (크롤링 필요) | 보류 |
| CME/CBOT | 선물 | 제한적 | 일부 무료 | 금·밀·옥수수 | 보류 |
| Investing.com | 원자재 | 크롤링 | 무료 | 나프타·에틸렌 스프레드 | 보류 |

### ⑤ 무역·공급망

| Source | 커버리지 | API | 무료 | 특징 | 어댑터 |
|---|---|---|---|---|---|
| **UN Comtrade** | 전세계 | REST | 완전무료 | HS코드 기준 품목별 무역량 | **TODO** `un_comtrade` |
| WTO | 전세계 | REST | 완전무료 | 관세·무역장벽 | TODO 보류 |
| KITA (무역협회) | 한국 | REST | 완전무료 | 품목별 수출입 상세 | TODO 3순위 |

### ⑥ 심리·대안 데이터

| Source | 커버리지 | API | 무료 | 특징 | 어댑터 |
|---|---|---|---|---|---|
| **Google Trends** | 글로벌 검색 | `pytrends` | 완전무료 | 산업 관심도 (선행지표 후보) | **TODO** `pytrends` |
| **CFTC COT** | 미국 선물 | REST | 완전무료 | 기관 포지션 (주간) | **TODO** `cftc` |
| Fear & Greed | 미국 | 크롤링 | 무료 | CNN 시장 심리 지수 | TODO 보류 |
| Reddit/X | 글로벌 | REST | 제한적 | 개인투자자 심리 | TODO 보류 |

---

## 활용도 분류

### 🟢 바로 사용 가능 (완전무료 + 안정 API)
- 핵심 축: FRED · KOSIS · ECOS · EIA · yfinance · pykrx
- 보조 축: OECD · World Bank · DART · 관세청 · UN Comtrade

### 🟡 제한적 사용
- Alpha Vantage · Polygon (rate limit)
- pytrends · Fear & Greed (비공식)
- LME · Investing.com (크롤링)

### 🔴 유료 / 불안정
- Bloomberg · Refinitiv · FactSet
- 실시간 선물 (CME/CBOT)

---

## 1순위 어댑터 추가 시나리오

### A. `yfinance` — 글로벌 가격 + 섹터 메타
글로벌 ETF·해외주식·섹터 인덱스를 한번에. KIS의 해외시세 어댑터 대체/보완.
한국 종목도 `005930.KS` 형태로 조회 가능 (보조 검증용).

### B. `pykrx` — KRX 공식 업종지수
KIS는 실시간이 강하지만 **과거 업종지수·투자자동향**은 pykrx가 압도적.
백테스트 시 KRX 공식 데이터를 기준으로 한 번 더 검증.

### C. `oecd` — 경기선행지수 CLI
선진국 CLI(Composite Leading Indicator)는 6-9개월 선행. 매크로 사이클 감지의 핵심.
SDMX REST: `https://stats.oecd.org/SDMX-JSON/data/MEI_CLI/...`

### D. `worldbank` — 장기 GDP·산업비중
화학섹터 같은 업황 분석할 때 글로벌 GDP·산업 비중 trend가 필수.
`https://api.worldbank.org/v2/country/all/indicator/NV.IND.MANF.ZS`

### E. `customs` (관세청 TRASS) — HS코드별 실시간 수출입
**화학섹터·반도체섹터에 가장 중요한 선행지표.**
HS 3901-3926 (석유화학), HS 8542 (반도체) 등 품목별 월별 수출입.
사장님 11년 화학 도메인과 직결.

---

## 화학섹터 사례 — 4개 소스 조합

> 사장님 도메인 특화 케이스: "화학섹터 모멘텀이 진짜 살아있는지" 추적하려면

| 신호 | 데이터 | 소스 |
|---|---|---|
| 정제시설 가동률 ↑ | Refinery Utilization | **EIA** ✓ |
| 에틸렌 생산량 ↑ | Ethylene Production | **EIA** ✓ |
| 화학공업 생산지수 ↑ | KOSIS 코드 D40 | **KOSIS** ✓ |
| 출하지수 ↑ | KOSIS 코드 D45 | **KOSIS** ✓ |
| 석유화학 수출 ↑ | HS 3901-3926 | **TRASS (TODO)** |
| 나프타-WTI 스프레드 | FRED + EIA | **FRED** + **EIA** ✓ |

→ 5개 중 4개는 이미 어댑터가 있음. **관세청 TRASS만 추가하면 화학섹터 모멘텀 모델 완성.**

---

## 다음 액션

1. **TODO 1순위 어댑터 5개 PR**:
   - `yfinance` (즉시) — `pip install yfinance`로 끝
   - `pykrx` (즉시) — `pip install pykrx`로 끝
   - `customs` (TRASS API 키 발급 필요) — 화학섹터 모멘텀 완성도 핵심
   - `oecd` (즉시) — SDMX-JSON 직접 호출
   - `worldbank` (즉시) — REST 직접 호출
2. **n8n 워크플로우 분리**: 정적(배치 일별) vs 동적(실시간)
3. **5개 파일럿 섹터 (반도체·화학·자동차·은행·조선) 지표 매핑** — 각 섹터당 10개 지표, 실물·매크로 지표 60% 이상

---

## 출처
원본 메모: `~/.ky-platform/finance.ini` — 사장님이 작성한 데이터 소스 지형도 정리.
