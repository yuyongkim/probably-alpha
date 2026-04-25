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

## 디스크 레이아웃 (2026-04-25 기준 — 최신)

```
~/.ky-platform/data/sectors/        총 164 파일, 327,611 rows, 48.5 MB
├── _manifest.json                ← 최근 API 수집 결과
├── customs/        24개   38.1MB  HS 코드 × 12개월 × 국가
├── dart/           36개    1.2MB  18 섹터 대표 종목 × 2년 사업보고서
├── fred/           19개    1.1MB  매크로 시리즈 2014→
├── kosis/           1개  874.6KB  GDP by 경제활동 분기 (22 산업)
├── ecos/            7개  626.5KB  한국 기준금리·국채·환율·CSI
├── oecd/            5개   45.8KB  CLI 5개국 120개월
├── pytrends/       16개   30.5KB  검색관심도 키워드
├── cftc/            5개   20.6KB  COT 1년
├── worldbank/       6개    7.9KB  GDP·산업비중·인구
├── un_comtrade/     4개  487.0B   HS 글로벌 cross-check
└── imported/                      Economic_analysis 임포트 (Nov 2025)
    ├── ecos/       15개    4.2MB
    ├── fred/       22개    2.2MB
    └── krx/         4개  114.5KB
```

저장소(`data/`)에는 매니페스트만 커밋합니다 (실데이터는 .gitignore).
디스크 진실 스냅샷은 `python scripts/summarize_data.py`로 언제든 재생성.

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

### API 수집 — 142 specs (2026-04-26)

| 출처 | 셀 수 | 결과 | 비고 |
|---|---|---|---|
| customs | 28 | OK 28/28 | HS 24종 12개월 + 10일 잠정 4종 (수출/수입 × 국가/품목). endpoint 5/6 verified, 1개 (HS 단독 월별)는 권한 활성화 대기 |
| dart | 36 | OK 36/36 | 18 섹터 대표 종목 × 2년 사업보고서 (corp_code 모두 검증) |
| fred | 19 | OK 19/19 | Fed Funds·Treasury·SP500·산업생산·VIX 등 2014→ |
| ecos | 7 | OK 7/7 | 한국 기준금리·국고채 3Y/10Y·회사채 AA-·환율·CSI |
| eia | 9 | OK 8/9 | WTI·Brent·정제가동률·휘발유·재고·천연가스 (1개 frequency 미세 오류) |
| kosis | 1 | OK 1/1 | GDP by 경제활동 (한은) — 22 산업 × 40 분기 = 2200 rows |
| kis_index | 6 | OK 6/6 | KOSPI/KOSDAQ/200 + 음식료/섬유/종이 6 인덱스 일별 50일 |
| oecd | 5 | OK 5/5 | KOR·USA·CHN·JPN·DEU CLI 120개월 |
| worldbank | 6 | OK 6/6 | KOR/CHN/USA GDP·제조업비중·인구·고령화 25년 |
| pytrends | 16 | △ transient | 첫 실행 16/16 OK; 같은 세션 재실행 시 Google rate-limit. 디스크에 잔존 |
| cftc | 5 | OK 5/5 | 원유·금·구리·엔·유로 COT 1년 |
| un_comtrade | 4 | OK 4/4 | 한국→세계 HS 4종 비교 |

### 임포트 — 41 specs

`Economic_analysis/economic_indicator/data/raw/` (2025-11-08 수집분)에서 가져옴:

| 출처 | 시리즈 수 | 대표 시리즈 |
|---|---|---|
| imported_ecos | 15 | 기준금리·3-30Y 국고채·CD91·M2·고용률·실업률·CPI·Core CPI·BSI·CSI·코스피·코스닥·회사채3Y |
| imported_fred | 22 | GDP·CPI·Core CPI·Fed Funds·Treasury 2/10/30Y·SP500·NASDAQ·Dow·Dollar Index·Industrial Production·Nonfarm Payrolls·Oil·PCE·Retail Sales·Consumer Sentiment 등 |
| imported_krx | 4 | 코스피·코스닥 지수 월별 |

### 합계 (2026-04-26 기준)

- **183개 시리즈** 디스크 보유
- **24.9MB** raw CSV (customs HS 데이터가 가장 큼)
- **WICS 34섹터 매트릭스 커버리지: 292/340 = 85.9%**
- 셀 단위 진척: `python scripts/sector_coverage.py`

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

## 알려진 한계 (2026-04-26 갱신)

1. **customs**: 사실상 모든 케이스 functional. 2026-04-26 시점:
   - ✓ `nitemtrade/getNitemtradeList` 한 endpoint가 HS×국가 + HS만 + 국가만 모든 모드 처리
   - ✓ 4 종 10일 잠정 (cntyMmUtPrviExp/Imp + prlstMmUtPrviExp/Imp)
   - ` Itemtrade/getItemtradeList` 는 data.go.kr이 별도 page로 listing하지만 nitemtrade(cntyCd 미지정)와 동일 데이터 — 사용 안 해도 됨
2. **pytrends Google rate-limit** — 같은 세션에서 재실행 시 차단됨. 새 세션 또는 30분-1시간 대기 후 회복. 디스크의 16 CSVs는 첫 실행에서 이미 확보.
3. **un_comtrade preview tier** — 최신 6개월 lag.
4. **KOSIS 산업별 생산지수 미수집** — 광공업 동향조사 tbl_id 미공개. 한은 GDP by 경제활동(DT_200Y105) 1건만 동작. 추후 KOSIS 사이트에서 정확한 tblId 확인 필요.
5. **OECD CLI** — 대부분 국가 한 달치 lag (예: 2026-02 데이터가 4월에 확정 반영).
6. **KIS 업종지수 0040+ 코드 (화학/철강/전기전자 등 17 sub-index)** — 응답 0 rows. KIS 별도 코드 시스템. KIS 페이지네이션도 추가 필요 (1콜=50일 한계).
7. **BDI/SCFI/클락슨/DRAMeXchange/LME** — 안정 크롤링 소스 부재. tradingeconomics는 봇 차단. 63셀 영향.

---

## 다음 확장 후보 (2026-04-26 갱신)

이미 진행한 항목 ✓ 표시:
- ✓ DART 18 종목 × 2년 사업보고서 (corp_code 모두 검증)
- ✓ EIA 9 시리즈 (WTI·Brent·정제가동률·휘발유·재고·천연가스)
- ✓ KIS 업종지수 6개 (KOSPI/KOSDAQ/200 + 음식료/섬유/종이)
- ✓ customs 10일 잠정 4 endpoint (수출/수입 × 국가/품목)

남은 후보:
- **KIS 업종지수 0040+ 17 sub-index** — KIS 별도 코드 시스템 lookup 필요
- **KIS 페이지네이션** — 12개월 OHLCV (현재 50일 한계)
- **KOSIS 산업별 생산지수** — 정확한 tblId 확인 후 7-15셀
- **ECOS 신용스프레드 / 부동산** — 정확한 stat_code/item_code 확인 후 5-10셀
- **SCFI / BDI / 클락슨 / DRAMeXchange 크롤러** — 안정 소스 발굴 시
- **customs `Itemtrade/getItemtradeList`** — data.go.kr 권한 활성화 자동 대기 중

---

## 매핑

`docs/SECTOR_INDICATOR_MAP.md` 의 어느 셀이 어떤 출처로 채워졌는지는
`_manifest.json` + `imported/_manifest.json` 의 `entries[].sector` × `source` 조합으로 추적합니다.
