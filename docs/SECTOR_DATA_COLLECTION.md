# 섹터 데이터 수집 (Sector Data Collection)

> WICS 34 섹터 인디케이터 매트릭스의 실제 시계열을 수집하는 파이프라인.
> 코드: `scripts/collect_sectors.py` + `packages/core/ky_core/sectors/registry.py`

---

## 출력 위치

```
~/.ky-platform/data/sectors/
├── _manifest.json                    ← 어떤 셀이 OK / FAIL 인지 인덱스
├── customs/                          ← 24 HS 코드 × 12개월 × 국가별 (~39MB)
├── fred/                             ← 19 매크로 시리즈 (~1.2MB)
├── oecd/                             ← 5 CLI 시리즈 × 120개월 (~64KB)
├── worldbank/                        ← 6 장기 지표 × 25년 (~28KB)
├── pytrends/                         ← 16 검색관심도 키워드 × 53주 (~68KB)
├── cftc/                             ← 5 COT 마켓 × 52주 (~36KB)
└── un_comtrade/                      ← 4 HS 글로벌 비교 (~8KB)
```

총 **79개 셀, 40MB**. `data/sectors_manifest_<DATE>.json` 으로 매니페스트는
저장소에 커밋합니다 (실데이터는 .gitignore).

---

## 매니페스트 스키마

```json
{
  "started_at": "2026-04-25T...Z",
  "finished_at": "2026-04-25T...Z",
  "total_specs": 79,
  "succeeded": 75,
  "failed": 4,
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
      "params": {"hs_code": "8542", "year_month_start": "202505", ...}
    }
  ]
}
```

---

## 실행 방법

```bash
# 전체 79셀 수집 (약 2분)
python scripts/collect_sectors.py

# 한 출처만
python scripts/collect_sectors.py --source customs
python scripts/collect_sectors.py --source pytrends

# 미리 보기 (호출 없이)
python scripts/collect_sectors.py --dry-run
```

---

## 수집 결과 (2026-04-25 1차 실행)

### 출처별 성공 셀

| 출처 | 셀 수 | 결과 | 비고 |
|---|---|---|---|
| customs | 24 | ✓ 24/24 | HS 코드별 12개월 × 국가별 |
| fred | 19 | ✓ 19/19 | 2014년부터 일·월 데이터 |
| oecd | 5 | ✓ 5/5 | KOR·USA·CHN·JPN·DEU CLI 120개월 |
| worldbank | 6 | ✓ 6/6 | KOR/CHN/USA 매크로 25년 |
| pytrends | 16 | △ 12/16 | Google rate-limit → 4셀 transient FAIL (재실행 시 회복) |
| cftc | 5 | ✓ 5/5 | 원유·금·구리·엔·유로 COT 1년 |
| un_comtrade | 4 | ✓ 4/4 | 한국→세계 HS 4종 |
| **합계** | **79** | **75/79 = 95%** | pytrends 4건만 일시적 실패 |

### 데이터 샘플

**customs/HS 8542 (메모리·반도체) 12개월**
```
period,hs_code,country,export_usd,import_usd,trade_balance_usd
총계,        ,    ,166,975,307,051   60,966,510,407   106,008,796,644
2025.05,854231,AE,    22,752               0           22,752
...
```

**fred/FED 기준금리 시계열**
```
date,value,unit
2014-01-01,0.07,Percent
...
2026-04-01,4.33,Percent
```

**oecd/KOR CLI**
```
period,value
2024-01,100.27
2023-12,100.13
...
```

---

## 알려진 한계

1. **customs API 5/6은 미활성화** — data.go.kr에서 활용신청 후 자동승인 lag.
   현재는 `hs_country_monthly` 1개 endpoint만 검증됨. 나머지(품목별 단독,
   10일 잠정치 4종)는 승인 후 자동으로 동작.
2. **pytrends Google rate-limit** — 16건 연속 호출 시 후반 4건이 transient
   `/sorry/index?` 응답을 받음. 30초 휴식 후 재시도 가능.
3. **un_comtrade preview tier** — 최신 데이터는 보통 6개월 lag.
4. **OECD CLI** — 대부분 국가는 한 달치 lag (예: 2026-02 데이터가 4월에
   확정 반영).

---

## 다음 확장 후보

- KOSIS 시리즈를 등록부에 추가 (산업별 생산/출하/재고 지수, 산업별 수출 등) — 약 +30셀
- ECOS 추가 (회사채 신용스프레드, 가계대출, 부동산 가격) — 약 +15셀
- DART 분기 실적 자동화 — 5대 그룹사 × 4분기 = +20셀
- KIS 업종지수 일별 — 34섹터 × 일별 = 백테스트용 가격 축

---

## 매핑

`docs/SECTOR_INDICATOR_MAP.md`의 어느 셀이 어떤 출처로 채워졌는지는
`_manifest.json`의 `entries[].sector` + `entries[].source` 조합으로 추적합니다.
