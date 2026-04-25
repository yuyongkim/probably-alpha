"""Sector indicator registry — concrete parameters for the WICS-34 map.

Each entry pins a specific (sector, indicator_name, source, **params) tuple
so ``scripts/collect_sectors.py`` can iterate the matrix and pull data
without per-call configuration.

Registry rows are intentionally redundant when the same indicator (e.g. KIS
업종지수) repeats across sectors — that mirrors how the user actually scans
sectors in parallel and keeps the collector code uniform.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class IndicatorSpec:
    sector: str            # WICS sector key, e.g. "semiconductor"
    sector_label: str      # human label
    name: str              # short indicator name
    source: str            # adapter id (matches CustomsAdapter.source_id etc.)
    method: str            # adapter method name to call
    params: dict[str, Any] = field(default_factory=dict)
    note: str = ""

    @property
    def slug(self) -> str:
        clean = self.name.replace(" ", "_").replace("/", "_")
        return f"{self.sector}__{clean}"


# ---------------------------------------------------------------------------
# Customs HS codes — Korean export-driven sectors.
# Format: (sector, sector_label, name, hs_code).
# Single hs_code per row; multi-HS sectors register multiple rows.
# ---------------------------------------------------------------------------

CUSTOMS_HS = [
    ("semiconductor", "반도체",     "메모리·반도체 수출 (HS 8542)",            "8542"),
    ("display",       "디스플레이",  "디스플레이 모듈 수출 (HS 8528)",          "8528"),
    ("handset",       "핸드셋",     "휴대폰 수출 (HS 8517)",                "8517"),
    ("auto",          "자동차",     "자동차 부품 수출 (HS 8708)",             "8708"),
    ("auto",          "자동차",     "자동차 완성차 수출 (HS 8703)",            "8703"),
    ("chemical",      "화학",      "기초 폴리머 수출 (HS 3901)",              "3901"),
    ("chemical",      "화학",      "PE/PP 수출 (HS 3902)",                  "3902"),
    ("chemical",      "화학",      "기타 폴리머 수출 (HS 3907)",              "3907"),
    ("chemical",      "화학",      "플라스틱 제품 수출 (HS 3923)",            "3923"),
    ("steel",         "철강",      "철강제품 수출 (HS 7208-7229 대표 HS72)",  "72"),
    ("nonferrous",    "비철금속",   "구리 (HS 74)",                          "74"),
    ("nonferrous",    "비철금속",   "알루미늄 (HS 76)",                      "76"),
    ("nonferrous",    "비철금속",   "아연 (HS 79)",                          "79"),
    ("ship",          "조선",      "선박 부품 (HS 8906)",                   "8906"),
    ("ship",          "조선",      "선박 완성품 (HS 8901)",                  "8901"),
    ("machinery",     "기계",      "일반기계 (HS 84)",                      "84"),
    ("electric",      "전기장비",   "전기장비 (HS 85 — 8542 제외 추정)",       "85"),
    ("paper",         "종이·목재",  "펄프 (HS 47)",                          "47"),
    ("paper",         "종이·목재",  "종이 (HS 48)",                          "48"),
    ("food",          "식품",      "농수산식품 (HS 16-22 대표 HS16)",         "16"),
    ("pharma",        "제약",      "의약품 (HS 30)",                         "30"),
    ("cosmetic",      "화장품",    "화장품 (HS 3304)",                       "3304"),
    ("energy",        "에너지",    "석유제품 (HS 2710)",                     "2710"),
    ("energy",        "에너지",    "원유 수입 (HS 2709)",                    "2709"),
]


def _customs_specs() -> list[IndicatorSpec]:
    """data.go.kr 관세청 API enforces a max 12-month window per call. We pull
    the most recent 12 months in a single shot; for longer history the
    collector can be extended to chunk multi-year requests."""
    out: list[IndicatorSpec] = []
    for sector, label, name, hs in CUSTOMS_HS:
        out.append(
            IndicatorSpec(
                sector=sector,
                sector_label=label,
                name=name,
                source="customs",
                method="get_hs_country_monthly",
                params={
                    "hs_code": hs,
                    "year_month_start": "202505",
                    "year_month_end": "202604",
                    "num_rows": 1000,
                },
                note=f"HS {hs}",
            )
        )
    # 10-day provisional (verified 2026-04-26) — country & item dimensions.
    # priodYear / priodMon / priodDt + itemUsdAmt00..10 (00=총합, 01-10=TOP 10).
    for dim, dim_label, flow, method in (
        ("country", "국가별", "export", "get_10day_export_by_country"),
        ("country", "국가별", "import", "get_10day_import_by_country"),
        ("item",    "주요품목", "export", "get_10day_export_by_item"),
        ("item",    "주요품목", "import", "get_10day_import_by_import_by_item" if False else "get_10day_import_by_item"),
    ):
        out.append(
            IndicatorSpec(
                sector="trade",
                sector_label="무역",
                name=f"{dim_label} 10일 잠정 {flow.upper()}",
                source="customs",
                method=method,
                params={
                    "year_month_start": "202604",
                    "year_month_end":   "202604",
                    "num_rows": 200,
                },
                note=f"{flow} 10-day {dim} provisional",
            )
        )
    # 국가별 월 누적 — 주요 5개 무역국 (US/CN/JP/VN/DE) 12개월
    for cnty, name in [
        ("US", "미국"), ("CN", "중국"), ("JP", "일본"),
        ("VN", "베트남"), ("DE", "독일"),
    ]:
        out.append(
            IndicatorSpec(
                sector="trade",
                sector_label="무역",
                name=f"국가별 월 — {name}({cnty})",
                source="customs",
                method="get_country_monthly",
                params={
                    "country_code": cnty,
                    "year_month_start": "202505",
                    "year_month_end":   "202604",
                    "num_rows": 1000,
                },
                note=f"country={cnty}",
            )
        )
    return out


# ---------------------------------------------------------------------------
# FRED — global macro that recurs across many sectors. Pull each series once;
# multiple sectors can read from the same dump.
# ---------------------------------------------------------------------------

FRED_SERIES = [
    ("macro", "FED 기준금리",         "FEDFUNDS"),
    ("macro", "10Y Treasury",       "DGS10"),
    ("macro", "2Y Treasury",        "DGS2"),
    ("macro", "10Y-2Y 스프레드",      "T10Y2Y"),
    ("macro", "10Y-3M 스프레드",      "T10Y3M"),
    ("macro", "30Y Mortgage Rate",  "MORTGAGE30US"),
    ("macro", "Dollar Index (DXY)", "DTWEXBGS"),
    ("macro", "VIX 변동성지수",       "VIXCLS"),
    ("macro", "Industrial Production", "INDPRO"),
    ("macro", "Capacity Utilization",  "TCU"),
    ("auto",   "미국 신차 SAAR (TOTALSA)", "TOTALSA"),
    ("retail", "미국 소매판매",          "RSAFS"),
    ("retail", "미국 소비자신뢰지수",      "UMCSENT"),
    ("construction", "미국 신규주택착공", "HOUST"),
    ("oil",    "WTI 원유",              "DCOILWTICO"),
    ("oil",    "Brent 원유",            "DCOILBRENTEU"),
    ("macro",  "미국 ISM 제조업 신규수주", "NEWORDER"),
    ("macro",  "PCE Inflation",          "PCEPI"),
    ("macro",  "Core CPI",              "CPILFESL"),
]


def _fred_specs() -> list[IndicatorSpec]:
    out: list[IndicatorSpec] = []
    for sector, name, sid in FRED_SERIES:
        out.append(
            IndicatorSpec(
                sector=sector,
                sector_label="매크로",
                name=name,
                source="fred",
                method="get_series",
                params={"series_id": sid, "start": "2014-01-01"},
                note=sid,
            )
        )
    return out


# ---------------------------------------------------------------------------
# OECD CLI — major economies. The CLI dataflow is ``DSD_STES@DF_CLI``.
# ---------------------------------------------------------------------------

OECD_CLI_COUNTRIES = ["KOR", "USA", "CHN", "JPN", "DEU"]


def _oecd_specs() -> list[IndicatorSpec]:
    return [
        IndicatorSpec(
            sector="macro",
            sector_label="매크로",
            name=f"OECD CLI {country}",
            source="oecd",
            method="get_cli",
            params={"country_iso": country, "recent": 120},
            note=f"Composite Leading Indicator — {country}",
        )
        for country in OECD_CLI_COUNTRIES
    ]


# ---------------------------------------------------------------------------
# World Bank — KOR + major trading partners; long-run structural metrics.
# ---------------------------------------------------------------------------

WORLDBANK_INDICATORS = [
    ("KOR", "NY.GDP.MKTP.CD",    "한국 명목 GDP (USD)"),
    ("KOR", "NV.IND.MANF.ZS",    "한국 제조업 GDP 비중 (%)"),
    ("CHN", "NY.GDP.MKTP.KD.ZG", "중국 GDP 성장률"),
    ("USA", "NY.GDP.MKTP.KD.ZG", "미국 GDP 성장률"),
    ("KOR", "SP.POP.TOTL",       "한국 인구"),
    ("KOR", "SP.POP.65UP.TO.ZS", "한국 65세 이상 비중"),
]


def _worldbank_specs() -> list[IndicatorSpec]:
    return [
        IndicatorSpec(
            sector="macro",
            sector_label="매크로",
            name=name,
            source="worldbank",
            method="get_indicator",
            params={"country_iso": iso, "indicator": ind, "date_range": "2000:2024"},
            note=ind,
        )
        for iso, ind, name in WORLDBANK_INDICATORS
    ]


# ---------------------------------------------------------------------------
# pytrends — Korean sentiment keywords aligned to WICS sectors.
# ---------------------------------------------------------------------------

PYTRENDS_KEYWORDS = [
    ("semiconductor", "GPU"),
    ("semiconductor", "HBM"),
    ("semiconductor", "메모리 반도체"),
    ("display",       "OLED"),
    ("handset",       "iPhone"),
    ("handset",       "Galaxy"),
    ("auto",          "전기차"),
    ("auto",          "EV"),
    ("retail",        "쿠팡"),
    ("media",         "K-pop"),
    ("media",         "K-drama"),
    ("cosmetic",      "K-beauty"),
    ("food",          "라면"),
    ("pharma",        "GLP-1"),
    ("ship",          "조선"),
    ("defense",       "방산"),
]


def _pytrends_specs() -> list[IndicatorSpec]:
    return [
        IndicatorSpec(
            sector=sector,
            sector_label=sector,
            name=f"검색관심도 '{kw}'",
            source="pytrends",
            method="interest_over_time",
            params={"keywords": [kw], "geo": "KR", "timeframe": "today 12-m"},
            note=kw,
        )
        for sector, kw in PYTRENDS_KEYWORDS
    ]


# ---------------------------------------------------------------------------
# CFTC COT — commodity / FX positioning.
# ---------------------------------------------------------------------------

CFTC_MARKETS = [
    "CRUDE OIL",
    "GOLD",
    "COPPER",
    "JAPANESE YEN",
    "EURO FX",
]


def _cftc_specs() -> list[IndicatorSpec]:
    return [
        IndicatorSpec(
            sector="macro",
            sector_label="매크로",
            name=f"COT — {m}",
            source="cftc",
            method="search_market",
            params={"market_keyword": m, "limit": 52},
            note=m,
        )
        for m in CFTC_MARKETS
    ]


# ---------------------------------------------------------------------------
# ECOS (한국은행) — Korean rates, credit, sentiment, real estate.
# stat_code · item_code 조합은 한은 ECOS 통계검색에서 확정한 값 사용.
# (start/end YYYYMMDD for daily, YYYYMM for monthly, YYYY for annual.)
# ---------------------------------------------------------------------------

ECOS_SERIES = [
    # 금리 — 단·중·장기 + 회사채 신용스프레드
    ("macro",       "한국 기준금리",            "722Y001", "0101000", "M", "201501", "202604"),
    ("macro",       "콜금리(1일물)",            "722Y001", "0101100", "D", "20150101", "20260430"),
    ("macro",       "국고채 3Y",               "817Y002", "010200000", "D", "20150101", "20260430"),
    ("macro",       "국고채 10Y",              "817Y002", "010210000", "D", "20150101", "20260430"),
    ("macro",       "회사채 AA- 3Y",          "817Y002", "010320000", "D", "20150101", "20260430"),
    ("macro",       "회사채 BBB- 3Y",         "817Y002", "010330000", "D", "20150101", "20260430"),
    # 가계 / 부동산
    ("bank",        "가계대출 잔액",            "151Y005", "1000000",   "M", "201501", "202604"),
    ("realestate",  "주택매매가격지수 (전국)",   "901Y063", "S22A",      "M", "201501", "202604"),
    # 환율
    ("macro",       "원/달러 환율 (종가)",      "731Y001", "0000001",   "D", "20150101", "20260430"),
    ("macro",       "원/엔(100엔) 환율",        "731Y001", "0000002",   "D", "20150101", "20260430"),
    # 심리지표
    ("macro",       "BSI 제조업 업황",          "512Y014", "AX1AA",     "M", "201501", "202604"),
    ("macro",       "CSI 종합소비자심리지수",    "511Y002", "FME",       "M", "201501", "202604"),
]


def _ecos_specs() -> list[IndicatorSpec]:
    out: list[IndicatorSpec] = []
    for sector, name, stat, item, freq, start, end in ECOS_SERIES:
        out.append(
            IndicatorSpec(
                sector=sector,
                sector_label="매크로" if sector == "macro" else sector,
                name=name,
                source="ecos",
                method="get_series",
                params={
                    "stat_code": stat,
                    "item_code": item,
                    "start": start,
                    "end": end,
                    "freq": freq,
                },
                note=f"{stat}/{item}",
            )
        )
    return out


# ---------------------------------------------------------------------------
# KOSIS (통계청) — 산업별 생산·출하·재고 지수.
# org_id=101 (통계청). tblId codes from the 광공업동향조사 family.
# Some entries leave item_code/obj_l1 None and let last_n_periods drive the
# window — KOSIS auto-returns the canonical default.
# ---------------------------------------------------------------------------

KOSIS_SERIES = [
    # 한국은행 분기별 GDP by 경제활동 (산업별) — verified working with ALL/ALL.
    # 22개 산업분류 × 분기 → 농림어업·제조업·서비스업·건설업 등 모두 포함.
    ("macro", "GDP by 경제활동 (분기)", "301", "DT_200Y105", "ALL", "ALL", "Q"),
    # 광공업 동향조사 산업별 생산지수 — 정확한 tblId 추후 확보 (현재 KOSIS API에
    # 안정적 endpoint 없음). Economic_analysis 임포트로 일부 보충됨.
]


def _kosis_specs() -> list[IndicatorSpec]:
    out: list[IndicatorSpec] = []
    for sector, name, org_id, tbl_id, item_code, obj_l1, prd_se in KOSIS_SERIES:
        out.append(
            IndicatorSpec(
                sector=sector,
                sector_label=sector,
                name=name,
                source="kosis",
                method="get_data",
                params={
                    "org_id": org_id,
                    "tbl_id": tbl_id,
                    "item_code": item_code,
                    "obj_l1": obj_l1,
                    "prd_se": prd_se,
                    "last_n_periods": 40,  # 10년 분기
                },
                note=f"{org_id}/{tbl_id}/{item_code}/{obj_l1}",
            )
        )
    return out


# ---------------------------------------------------------------------------
# EIA — US energy series referenced across 화학·에너지·자동차·운송·유틸리티.
# v2 endpoints use path + series_code. We use both routes:
#   - get_series(series_id) for the "seriesid" legacy compat ones
#   - get_path_series(path, series_code) for v2 weekly/monthly paths
# ---------------------------------------------------------------------------

EIA_SERIES = [
    # (sector, name, method, args)
    ("energy",   "WTI 원유 (현물)",    "get_path_series",
        {"path": "petroleum/pri/spt", "series_code": "RWTC", "frequency": "daily", "length": 1500}),
    ("energy",   "Brent 원유 (현물)",  "get_path_series",
        {"path": "petroleum/pri/spt", "series_code": "RBRTE", "frequency": "daily", "length": 1500}),
    ("energy",   "미국 원유 재고 (Crude Stocks)", "get_path_series",
        {"path": "petroleum/stoc/wstk", "series_code": "WCESTUS1", "frequency": "weekly", "length": 520}),
    ("energy",   "미국 정제시설 가동률", "get_path_series",
        {"path": "petroleum/pnp/wiup", "series_code": "WPULEUS3", "frequency": "weekly", "length": 520}),
    ("chemical", "Heating Oil (#2 NY)", "get_path_series",
        {"path": "petroleum/pri/spt", "series_code": "EER_EPD2F_PE1_Y35NY_DPG", "frequency": "weekly", "length": 520}),
    ("oil",      "천연가스 (Henry Hub) 월별", "get_path_series",
        {"path": "natural-gas/pri/sum", "series_code": "RNGWHHD", "frequency": "monthly", "length": 240}),
    ("oil",      "정제가동률 가중평균",     "get_path_series",
        {"path": "petroleum/pnp/wiup", "series_code": "WPULEUS3", "frequency": "monthly", "length": 240}),
    ("auto",     "미국 휘발유 소매가",    "get_path_series",
        {"path": "petroleum/pri/gnd", "series_code": "EMM_EPMR_PTE_NUS_DPG", "frequency": "weekly", "length": 520}),
    ("transport","미국 디젤 도매가",     "get_path_series",
        {"path": "petroleum/pri/spt", "series_code": "EER_EPD2DXL0_PE_RGC_DPG", "frequency": "weekly", "length": 520}),
]


def _eia_specs() -> list[IndicatorSpec]:
    out: list[IndicatorSpec] = []
    for sector, name, method, params in EIA_SERIES:
        out.append(
            IndicatorSpec(
                sector=sector,
                sector_label=sector,
                name=name,
                source="eia",
                method=method,
                params=params,
                note=params.get("series_code", ""),
            )
        )
    return out


# ---------------------------------------------------------------------------
# DART — quarterly / annual financials for the major sector flagship.
# corp_code values from DART CORPCODE.xml (publicly available).
# ---------------------------------------------------------------------------

DART_FLAGSHIP = [
    # (sector, sector_label, corp_code, name) — verified against DART CORPCODE.xml 2026-04-25
    ("semiconductor", "반도체", "00126380", "삼성전자"),
    ("semiconductor", "반도체", "00164779", "SK하이닉스"),
    ("display",       "디스플레이", "00105873", "LG디스플레이"),
    ("chemical",      "화학",   "00126186", "LG화학"),
    ("chemical",      "화학",   "00631518", "SK이노베이션"),
    ("auto",          "자동차", "00164742", "현대자동차"),
    ("auto",          "자동차", "00106641", "기아"),
    ("ship",          "조선",   "01390344", "HD현대중공업"),
    ("ship",          "조선",   "00126478", "삼성중공업"),
    ("steel",         "철강",   "00126308", "POSCO홀딩스"),
    ("bank",          "은행",   "00688996", "KB금융지주"),
    ("bank",          "은행",   "00382199", "신한지주"),
    ("retail",        "유통",   "00872984", "이마트"),
    ("media",         "엔터",   "00258689", "JYP Ent."),
    ("cosmetic",      "화장품", "00356370", "LG생활건강"),
    ("food",          "식품",   "00635134", "CJ제일제당"),
    ("pharma",        "제약",   "00413046", "셀트리온"),
    ("defense",       "방산",   "00126566", "한화에어로스페이스"),
]

DART_REPORT_YEARS = [2024, 2025]  # 가장 최근 2년 — annual report only


def _dart_specs() -> list[IndicatorSpec]:
    out: list[IndicatorSpec] = []
    for sector, label, corp, name in DART_FLAGSHIP:
        for year in DART_REPORT_YEARS:
            out.append(
                IndicatorSpec(
                    sector=sector,
                    sector_label=label,
                    name=f"{name} 사업보고서 {year}",
                    source="dart",
                    method="get_financial_statements",
                    params={
                        "corp_code": corp,
                        "year": year,
                        "report_code": "11011",  # annual
                        "fs_div": "CFS",
                    },
                    note=f"{name}/{year}",
                )
            )
    return out


# ---------------------------------------------------------------------------
# KIS — KOSPI 업종지수 일별 OHLCV (12개월).
# FID_INPUT_ISCD codes from KRX 업종 분류. 매핑은 KOSPI 종합 + 11개 핵심
# 업종 + 코스닥 종합. WICS 34와 1:1은 아니지만 섹터 모멘텀 가격축에 충분.
# ---------------------------------------------------------------------------

KIS_INDEX_CODES = [
    # Verified-returning-50-rows codes (KIS returns max 50 daily rows per call,
    # ~10 weeks). Pagination + multi-call needed for longer history.
    ("market",        "KOSPI 종합",       "0001"),
    ("market",        "KOSDAQ 종합",      "1001"),
    ("market",        "KOSPI 200",        "2001"),
    ("food",          "KOSPI 음식료품",    "0010"),
    ("paper",         "KOSPI 섬유의복",    "0020"),
    ("paper",         "KOSPI 종이목재",    "0030"),
    # Codes 0040+ return 0 rows on the FHKUP03500100 endpoint; KIS uses a
    # different code system for finer 업종 indices that needs lookup.
    # Tracked as future work in CLAUDE.md.
]


def _kis_index_specs() -> list[IndicatorSpec]:
    out: list[IndicatorSpec] = []
    for sector, name, code in KIS_INDEX_CODES:
        out.append(
            IndicatorSpec(
                sector=sector,
                sector_label=sector,
                name=name,
                source="kis_index",
                method="get_index_daily",
                params={
                    "sector_code": code,
                    "date_from": "20250425",
                    "date_to": "20260425",
                    "period": "D",
                },
                note=f"KRX {code}",
            )
        )
    return out


# ---------------------------------------------------------------------------
# UN Comtrade — global view of Korea's HS exports for cross-validation.
# Limited to a handful since the public preview tier is lag-y and rate-limited.
# ---------------------------------------------------------------------------

COMTRADE_HS = ["8542", "8703", "3901", "8901"]


def _comtrade_specs() -> list[IndicatorSpec]:
    return [
        IndicatorSpec(
            sector="trade",
            sector_label="무역",
            name=f"Korea→World HS {hs}",
            source="un_comtrade",
            method="get_trade",
            params={
                "reporter_iso3": "KOR",
                "partner_iso3": "WLD",
                "hs_code": hs,
                "period": "202312",
                "flow": "X",
            },
            note=hs,
        )
        for hs in COMTRADE_HS
    ]


# ---------------------------------------------------------------------------
# Aggregate — public API
# ---------------------------------------------------------------------------

def all_specs() -> list[IndicatorSpec]:
    """Return only specs that hit external APIs.

    Note: ECOS and KOSIS series are NOT included here. The user already
    has 15 ECOS + 22 FRED + 4 KRX series collected at
    ``Economic_analysis/economic_indicator/data/raw/`` (Nov 2025). Those
    are imported via ``scripts/import_existing_data.py`` rather than
    re-fetched. The ``_ecos_specs`` / ``_kosis_specs`` definitions remain
    in this module as a parameter reference for when we add a "refresh
    imported series" pipeline later.
    """
    return [
        *_customs_specs(),
        *_fred_specs(),
        *_kosis_specs(),     # GDP by industry (only one verified)
        *_eia_specs(),       # 10 US energy series
        *_dart_specs(),      # 18 sector flagships × 2 years annual reports
        *_kis_index_specs(), # 23 KOSPI/KOSDAQ sector indices, daily 12-month OHLCV
        *_oecd_specs(),
        *_worldbank_specs(),
        *_pytrends_specs(),
        *_cftc_specs(),
        *_comtrade_specs(),
    ]


def specs_by_source(source: str) -> list[IndicatorSpec]:
    return [s for s in all_specs() if s.source == source]


def total_count() -> int:
    return len(all_specs())
