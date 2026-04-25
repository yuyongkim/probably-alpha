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
    return [
        *_customs_specs(),
        *_fred_specs(),
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
