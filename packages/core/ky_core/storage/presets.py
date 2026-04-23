"""Daily collection presets.

These are opinionated defaults — a curated set of macro series that the
platform expects to refresh every day (and that we backfill 10 years for on
first-run). The runner script reads these when called with
``--source all-macro``.

Each entry line documents the source, series identifier, frequency and a
human-readable label so the bulk-backfill log is self-explaining.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

# --------------------------------------------------------------------------- #
# FRED — U.S. macro                                                           #
# --------------------------------------------------------------------------- #
# Growth / inflation / liquidity / credit must all be covered so that
# compute_compass() (packages/core/ky_core/macro/compass.py) has at least one
# series per axis. BAA10Y/AAA10Y drive the credit axis.
FRED_SERIES: list[str] = [
    "GDP",
    "CPIAUCSL",
    "UNRATE",
    "FEDFUNDS",
    "DGS10",
    "DGS2",
    "DFF",
    "BAA10Y",
    "AAA10Y",
]

# --------------------------------------------------------------------------- #
# ECOS — Bank of Korea                                                        #
# --------------------------------------------------------------------------- #
# Each row: (stat_code, item_code, freq, description).
# Every code here has been validated against the live ECOS API as of 2026-04.
# Covers: policy rate · FX · inflation (CPI/core/PPI) · money (M1/M2) ·
# growth (GDP expenditure) · production · employment · leading indicators ·
# trade · housing · government bond yields. Together these give the macro
# compass a full Korean counterpart to the FRED-only coverage it had before.
ECOS_SERIES: list[tuple[str, str, str, str]] = [
    # --- rates & FX (daily) ---
    ("722Y001", "0101000", "D", "기준금리 (BoK base rate)"),
    ("731Y001", "0000001", "D", "원/달러 환율 (KRW/USD)"),
    ("817Y002", "010190000", "D", "국고채 3년 수익률"),
    ("817Y002", "010195000", "D", "국고채 10년 수익률"),
    ("817Y002", "010200000", "D", "국고채 20년 수익률"),
    # --- inflation (monthly) ---
    ("901Y009", "0",  "M", "CPI 총지수"),
    ("901Y010", "DB", "M", "근원 CPI (식료품·에너지 제외)"),
    ("901Y010", "QB", "M", "근원 CPI (농산물·석유류 제외)"),
    ("404Y014", "*AA", "M", "생산자물가지수 (PPI)"),
    # --- money & liquidity (monthly) ---
    ("161Y006", "BBHA00", "M", "M2 평잔 원계열"),
    ("161Y002", "BBLA00", "M", "M1 평잔 원계열"),
    # --- real activity (monthly) ---
    ("901Y033", "A00",   "M", "전산업생산지수"),
    ("901Y027", "I61BA", "M", "취업자수"),
    ("901Y027", "I61B",  "M", "경제활동인구"),
    ("901Y067", "I16A",  "M", "경기선행종합지수"),
    ("901Y067", "I16B",  "M", "경기동행종합지수"),
    ("403Y001", "*AA",   "M", "수출액"),
    # --- housing (monthly) ---
    ("901Y062", "P63A", "M", "주택매매가격지수"),
    ("901Y063", "P64A", "M", "주택전세가격지수"),
    # --- growth (quarterly, seasonally adjusted) ---
    ("200Y108", "10601", "Q", "실질 GDP (지출측, 계절조정, 분기)"),
]

# --------------------------------------------------------------------------- #
# KOSIS — Statistics Korea                                                    #
# --------------------------------------------------------------------------- #
# NOTE: KOSIS requires a per-table ``itmId`` and ``objL1`` which must be
# discovered by hand through the KOSIS OpenAPI portal
# (https://kosis.kr/openapi/). Until those IDs are curated we keep the list
# empty — the runner logs a warning and skips KOSIS rather than invent codes.
# Most of the macro content we would fetch here (retail sales, service
# production, consumer / business sentiment, housing) is already covered by
# the ECOS block above.
KOSIS_SERIES: list[dict[str, Any]] = []

# --------------------------------------------------------------------------- #
# EIA — U.S. energy                                                           #
# --------------------------------------------------------------------------- #
# The v2 REST API serves these as path + series facet rather than
# ``seriesid/{id}/data`` (which 404s for petroleum weeklies). We therefore
# carry (path, series_code, description) triples so the adapter can build the
# right URL.
EIA_SERIES: list[tuple[str, str, str]] = [
    ("petroleum/stoc/wstk", "WCESTUS1", "U.S. crude oil ending stocks (weekly, excl. SPR)"),
    ("petroleum/pnp/wiup",  "WPULEUS3", "U.S. refinery utilisation (%, weekly)"),
    ("natural-gas/stor/wkly", "NW2_EPG0_SWO_R48_BCF", "U.S. natural gas working storage (BCF, weekly)"),
]


def default_window(days: int = 365) -> tuple[str, str]:
    """ISO (start, end) window for macro backfills."""
    today = date.today()
    start = today - timedelta(days=days)
    return start.isoformat(), today.isoformat()


def yyyymmdd_window(days: int = 365) -> tuple[str, str]:
    today = date.today()
    start = today - timedelta(days=days)
    return start.strftime("%Y%m%d"), today.strftime("%Y%m%d")


# A single bundle the runner can consume.
MACRO_DAILY_PRESET: dict[str, Any] = {
    "fred": FRED_SERIES,
    "ecos": ECOS_SERIES,
    "kosis": KOSIS_SERIES,
    "eia": EIA_SERIES,
    "exim": [date.today().isoformat()],
}
