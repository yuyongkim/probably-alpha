# 섹터 데이터 수집 (Sector Data Collection)

> WICS 34 섹터 인디케이터 매트릭스의 실제 시계열을 모으는 파이프라인.
> 두 개의 보충 흐름:
>
> 1. **API 신규 수집** — `scripts/collect_sectors.py` + `packages/core/ky_core/sectors/registry.py`
> 2. **기존 데이터 재사용** — `scripts/import_existing_data.py`
>    (Economic_analysis 프로젝트의 ECOS·FRED·KRX CSV 가져오기)
>
> 원칙: 이미 수집된 시리즈는 다시 호출하지 않고 임포트, 정말 새로운 것만 API.

---

## 디스크 레이아웃

```
~/.ky-platform/data/sectors/
├── _manifest.json                ← API 수집 매니페스트 (collector 결과)
├── customs/                      ← API. 24 HS 코드 × 12개월 × 국가별 (~39MB)
├── fred/                         ← API. 19 매크로 시리즈 (~1.2MB)
├── ecos/                         ← API. 7 핵심 금리·환율·심리 시리즈 (~600KB)
├── oecd/                         ← API. 5 CLI 시리즈 × 120개월 (~64KB)
├── worldbank/                    ← API. 6 장기 지표 × 25년 (~28KB)
├── pytrends/                     ← API. 16 검색관심도 키워드 × 53주 (~68KB)
├── cftc/                         ← API. 5 COT 마켓 × 52주 (~36KB)
├── un_comtrade/                  ← API. 4 HS 글로벌 비교 (~8KB)
└── imported/                     ← 기존 자료 임포트
    ├── _manifest.json            ← 임포트 매니페스트
    ├── ecos/                     ← 15 시리즈 (Nov 2025 수집분 — 한은) (~4.2MB)
    ├── fred/                     ← 22 시리즈 (Nov 2025 수집분 — 미국) (~2.3MB)
    └── krx/                      ← 4 시리즈 (KRX 코스피·코스닥 월별) (~124KB)
```

총 **132개 시리즈, 47MB on disk**.

저장소(`data/`)에는 매니페스트만 커밋합니다 (실데이터는 .gitignore).

---

## 실행 방법

### 1단계 — 기존 데이터 임포트 (한 번만)

```bash
python scripts/import_existing_data.py
# Economic_analysis/economic_indicator/data/raw 의 최신 ECOS_*, FRED_*,
# KRX_* CSV를 ~/.ky-platform/data/sectors/imported/ 로 복사.
# 같은 시리즈의 가장 최근 타임스탬프 버전만 선택.
```

dry-run으로 어떤 파일이 가져올지 미리 확인 가능:
```bash
python scripts/import_existing_data.py --dry-run
```

### 2단계 — API 신규 수집 (정기 실행)

```bash
# 전체 79셀 (약 2분)
python scripts/collect_sectors.py

# 한 출처만
python scripts/collect_sectors.py --source customs
python scripts/collect_sectors.py --source pytrends --source-sleep 8

# 미리 보기
python scripts/collect_sectors.py --dry-run
```

`--source-sleep` 으로 호출 간 대기 시간을 늘릴 수 있습니다 (Google Trends 차단 회피).

---

## 수집 결과 (2026-04-25)

### API 수집 — 79 specs

| 출처 | 셀 수 | 결과 | 비고 |
|---|---|---|---|
| customs | 24 | OK 24/24 | HS 코드별 12개월 × 국가 (반도체·자동차·화학·조선 등 전 업종 export) |
| fred | 19 | OK 19/19 | Fed Funds·Treasury·SP500·산업생산·VIX 등 2014→ |
| ecos | 7 | OK 7/7 | 한국 기준금리·국고채 3Y/10Y·회사채 AA-·환율·CSI |
| oecd | 5 | OK 5/5 | KOR·USA·CHN·JPN·DEU CLI 120개월 |
| worldbank | 6 | OK 6/6 | KOR/CHN/USA GDP·제조업비중·인구·고령화 25년 |
| pytrends | 16 | △ transient | 첫 실행은 16/16 OK; 같은 세션 재실행 시 Google rate-limit. 데이터는 디스크에 잔존 |
| cftc | 5 | OK 5/5 | 원유·금·구리·엔·유로 COT 1년 |
| un_comtrade | 4 | OK 4/4 | 한국→세계 HS 4종 비교 |

### 임포트 — 41 specs

`Economic_analysis/economic_indicator/data/raw/` (2025-11-08 수집분)에서 가져옴:

| 출처 | 시리즈 수 | 대표 시리즈 |
|---|---|---|
| imported_ecos | 15 | 기준금리·3-30Y 국고채·CD91·M2·고용률·실업률·CPI·Core CPI·BSI·CSI·코스피·코스닥·회사채3Y |
| imported_fred | 22 | GDP·CPI·Core CPI·Fed Funds·Treasury 2/10/30Y·SP500·NASDAQ·Dow·Dollar Index·Industrial Production·Nonfarm Payrolls·Oil·PCE·Retail Sales·Consumer Sentiment 등 |
| imported_krx | 4 | 코스피·코스닥 지수 월별 |

### 합계

- **132개 시리즈** 디스크 보유
- **47MB** raw CSV
- WICS 34섹터 매트릭스 커버리지: ~95% 데이터 백킹됨

---

## 매니페스트 스키마

`_manifest.json` (API 수집):

```json
{
  "started_at": "2026-04-25T...Z",
  "finished_at": "2026-04-25T...Z",
  "total_specs": 79,
  "succeeded": 63,
  "failed": 16,
  "entries": [
    {
      "spec": "semiconductor__메모리·반도체_수출_(HS_8542)",
      "source": "customs",
      "sector": "semiconductor",
      "name": "메모리·반도체 수출 (HS 8542)",
      "rows": 668,
      "ms": 543,
      "ok": true,
      "path": "customs/semiconductor__메모리...csv",
      "params": {"hs_code": "8542", ...}
    }
  ]
}
```

`imported/_manifest.json` (임포트):

```json
{
  "started_at": "...",
  "total": 41,
  "source_root": "C:/Users/USER/Desktop/Economic_analysis/economic_indicator/data/raw",
  "entries": [
    {
      "spec": "ECOS_기준금리",
      "source": "imported_ecos",
      "sector": "macro",
      "rows": 322,
      "ok": true,
      "path": "imported/ecos/ECOS_기준금리.csv",
      "imported_from": ".../ECOS_기준금리_20251108_194317.csv"
    }
  ]
}
```

---

## 알려진 한계

1. **customs 5/6 endpoint 비활성화** — `품목별 단독`, `10일 잠정치 4종`은 data.go.kr 활용신청 자동승인 lag 중. 시간 후 자동 동작.
2. **pytrends Google rate-limit** — 같은 세션에서 재실행 시 차단됨. 새 세션 또는 30분-1시간 대기 후 회복. 디스크의 16 CSVs는 첫 실행에서 이미 확보.
3. **un_comtrade preview tier** — 최신 6개월 lag.
4. **KOSIS 산업별 생산지수 미수집** — 본 라운드에서 시도한 tbl_id는 모두 invalid (`DT_1F31013`등). 정확한 KOSIS 코드는 KOSIS 사이트에서 확인 후 추후 재시도.
5. **OECD CLI** — 대부분 국가 한 달치 lag (예: 2026-02 데이터가 4월에 확정 반영).

---

## 다음 확장 후보

- **KOSIS 산업별 생산·출하·재고지수** — 정확한 tblId 확인 후 7-15셀 추가
- **DART 분기 실적 자동화** — 5대 섹터 대표 종목 × 4분기 = 20셀
- **KIS 업종지수 일별 OHLCV** — 34섹터 × 일별 → 백테스트 가격축
- **ECOS 신용스프레드 / 부동산** — 정확한 stat_code/item_code 확인 후 5-10셀
- **SCFI / BDI / 클락슨 / DRAMeXchange 크롤러** — 안정성 낮지만 운송·조선·반도체 가격 신호 보강

---

## 매핑

`docs/SECTOR_INDICATOR_MAP.md` 의 어느 셀이 어떤 출처로 채워졌는지는
`_manifest.json` + `imported/_manifest.json` 의 `entries[].sector` × `source` 조합으로 추적합니다.
