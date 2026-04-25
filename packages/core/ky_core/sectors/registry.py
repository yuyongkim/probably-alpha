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
# DART — quarterly / annual financials for the major sector flagship.
# corp_code values from DART CORPCODE.xml (publicly available).
# ---------------------------------------------------------------------------

DART_FLAGSHIP = [
    # (sector, sector_label, corp_code, name)
    ("semiconductor", "반도체", "00126380", "삼성전자"),
    ("semiconductor", "반도체", "00164779", "SK하이닉스"),
    ("display",       "디스플레이", "00164755", "LG디스플레이"),
    ("chemical",      "화학",   "00126186", "LG화학"),
    ("chemical",      "화학",   "01093641", "SK이노베이션"),
    ("auto",          "자동차", "00164742", "현대자동차"),
    ("auto",          "자동차", "00164817", "기아"),
    ("ship",          "조선",   "01023432", "HD현대중공업"),
    ("ship",          "조선",   "00164826", "삼성중공업"),
    ("steel",         "철강",   "00126308", "POSCO홀딩스"),
    ("bank",          "은행",   "00688996", "KB금융지주"),
    ("bank",          "은행",   "00382199", "신한지주"),
    ("retail",        "유통",   "00138321", "이마트"),
    ("media",         "엔터",   "00138717", "JYP Ent."),
    ("cosmetic",      "화장품", "00125957", "LG생활건강"),
    ("food",          "식품",   "00266961", "CJ제일제당"),
    ("pharma",        "제약",   "00164718", "셀트리온"),
    ("defense",       "방산",   "01075058", "한화에어로스페이스"),
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
        *_dart_specs(),      # 18 sector flagships × 2 years annual reports
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
