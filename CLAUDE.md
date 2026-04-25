# CLAUDE.md
> Claude Code가 ky-platform 세션 시작 시 가장 먼저 읽는 파일.
> 컨텍스트 절약을 위해 짧고 포인터 위주로 유지합니다.

---

## 프로젝트 정체성

`ky-platform` (probably-alpha) — 한국 주식시장 통합 분석 플랫폼.
도메인: gazua.yule.pics
브랜치: `platform`
스택: Next.js 15 (apps/web) + FastAPI (apps/api) + Python core (packages/core, packages/adapters)

---

## 데이터 상태 — 매번 재수집 금지

**원칙**: 데이터는 이미 ~/.ky-platform/data/sectors/ 에 수집되어 있음.
새로 수집하기 전에 **먼저 manifest를 읽어 무엇이 있는지 확인**한다.

| 무엇을 알고 싶은가 | 어디를 본다 |
|---|---|
| 현재 디스크에 어떤 시리즈가 있는가 | `data/sectors_unified_manifest.json` |
| 마지막 API 수집 결과 (성공/실패) | `data/sectors_manifest_<DATE>.json` |
| 임포트된 기존 자료 (Economic_analysis) | `data/sectors_imported_manifest_<DATE>.json` |
| 어떤 어댑터가 어디에 매핑되는가 | `docs/DATA_SOURCES_CATALOG.md` |
| WICS 34 섹터 × 10 지표 매트릭스 | `docs/SECTOR_INDICATOR_MAP.md` |
| 수집 파이프라인 사용법 | `docs/SECTOR_DATA_COLLECTION.md` |

**디스크 진실 즉석 확인** (manifest가 stale할 때):
```bash
python scripts/summarize_data.py
```
→ 디스크 스캔 → per-source 행 수·바이트 표 + 통합 매니페스트 갱신.

---

## 무엇이 이미 있고 무엇이 없는가 (2026-04-25 후반 스냅샷)

**WICS 34섹터 매트릭스 커버리지: 292 / 340 셀 = 85.9%**
(`python scripts/sector_coverage.py` 로 언제든 재계산)

180+ 파일 수집 완료. 다음은 다시 호출 금지:

| 출처 | 셀 수 | 비고 |
|---|---|---|
| customs | 24 | HS×국가 12개월 (2025-05~2026-04) |
| dart | 36 | 18 섹터 대표 × 2년 사업보고서 (CORPCODE.xml로 정정 완료) |
| fred / imported_fred | 41 | 매크로 시리즈 합계 |
| ecos / imported_ecos | 22 | 한국 금리·환율·심리 |
| eia | 8 | WTI·Brent·정제가동률·휘발유·재고 등 |
| kosis | 1 | GDP by 경제활동 (분기) |
| kis_index | 6 | KOSPI 종합·KOSDAQ·200·음식료·섬유의복·종이목재 일별 50일 |
| oecd | 5 | CLI 5개국 |
| worldbank | 6 | 25년 장기지표 |
| pytrends | 16 | 검색관심도 |
| cftc | 5 | COT 포지션 |
| un_comtrade | 4 | HS 글로벌 비교 |
| imported_krx | 4 | 코스피·코스닥 |

**아직 안 된 것** (재시도/추가 작업 필요):
- customs 5/6 endpoint — data.go.kr 활용신청 자동승인 lag
- KOSIS 광공업 동향조사 산업별 — 정확한 tblId 미확보
- KIS 업종지수 0040+ 코드 (화학/철강/전기전자 등 17개 sub-index) — KIS 업종 코드 시스템 별도 lookup 필요
- KIS 업종지수 페이지네이션 (1콜=50일 한계, 12개월 만들려면 5-6콜 필요)
- BDI/SCFI/클락슨/DRAMeXchange — 안정 크롤링 소스 부재 (63셀 영향)

---

## 핵심 명령

```bash
# 데이터 현황 확인 (먼저 이거 실행)
python scripts/summarize_data.py

# 신규 수집 (전체)
python scripts/collect_sectors.py

# 한 출처만 (예: pytrends — Google rate-limit 회피)
python scripts/collect_sectors.py --source pytrends --source-sleep 8

# 기존 자료 임포트 (Economic_analysis Nov 2025 dump)
python scripts/import_existing_data.py

# 어댑터 헬스체크
python -c "from ky_adapters.customs import CustomsAdapter; \
           print(CustomsAdapter.from_settings().healthcheck_all())"

# 모바일 QA (live 사이트 4 viewport)
python scripts/mobile_qa.py
```

---

## 정책 (어댑터 / 코드)

- 어댑터는 `packages/adapters/ky_adapters/<source>/`에 위치
- 모든 어댑터는 `BaseAdapter` 상속 + `healthcheck()` / `from_settings()` 구현
- API 키는 `~/.ky-platform/shared.env` (커밋 금지)
- KIS-only 정책: KR quotes는 KIS만 사용. yfinance/Kiwoom/Naver 어댑터 추가 금지
  (단 naver_fnguide는 재무제표 한정 예외)

---

## 다음 진행 (체크리스트 포맷)

이미 진행 중인 작업은 task list 참조. 신규 작업 시 다음 항목들이 백로그에
있음 — 사장님 우선순위 결정 시까지 보류:

- [ ] data.go.kr customs 5 endpoint 활성화 후 자동 재호출
- [ ] KOSIS 광공업 동향조사 정확한 tblId 확보 (KOSIS 사이트 직접 검색)
- [ ] KIS 업종지수 일별 OHLCV TR (FHKST03010100) 어댑터 추가
- [ ] DART 0행 반환 종목 corp_code 정정 (CORPCODE.xml 다운로드 필요)
- [ ] BDI/SCFI 크롤러 — 안정 소스 발굴 후 (현재 tradingeconomics는 봇 차단)

---

## 참고

ky-platform 자매 프로젝트:
- `Company_Credit/` — SEPA 전략 (별도 repo, KOSPI 주도주 탐지)
- `Economic_analysis/economic_indicator/` — 기존 매크로 시계열 dump (임포트 소스)
- `Finance_analysis/` — KOSIS/DCF 도구 (참고용)
- `QuantPlatform/knowledge/` — RAG용 도서 PDF (147+)
