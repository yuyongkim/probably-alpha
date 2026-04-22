"""Daily collection presets.

These are opinionated defaults — a minimal set of macro series that the
platform expects to refresh every day. The runner script reads these when
called with ``--source all-macro``.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

# FRED — U.S. macro
FRED_SERIES: list[str] = [
    "GDP",
    "CPIAUCSL",
    "UNRATE",
    "FEDFUNDS",
    "DGS10",
    "DGS2",
    "DFF",
]

# ECOS — Bank of Korea. Each row: (stat_code, item_code, freq, description)
ECOS_SERIES: list[tuple[str, str, str, str]] = [
    ("722Y001", "0101000", "D", "기준금리 (Base rate)"),
    ("731Y001", "0000001", "D", "원/달러 환율 (KRW/USD)"),
    ("101Y003", "BBHA00", "M", "M2 광의통화"),
]

# EIA — energy
EIA_SERIES: list[str] = [
    "PET.WCESTUS1.W",  # U.S. crude oil ending stocks (weekly)
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


# A single bundle the runner can consume
MACRO_DAILY_PRESET: dict[str, Any] = {
    "fred": FRED_SERIES,
    "ecos": ECOS_SERIES,
    "eia": EIA_SERIES,
    "exim": [date.today().isoformat()],
}
