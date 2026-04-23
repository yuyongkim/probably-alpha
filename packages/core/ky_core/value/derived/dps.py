"""DPS (dividend per share) timeseries + 10-year aristocrat detection.

Primary source: ``dividend_history`` (DART 배당공시 → DPS, payout_ratio,
yield per fiscal year). When that table is empty for a symbol we fall
back to deriving DPS from the fnguide snapshot as
``DPS ≈ dividend_yield × price``.

An aristocrat — here — is a symbol that booked **≥10 consecutive years
of positive, non-decreasing DPS** (we allow one flat year; any cut
breaks the streak). The streak is computed trailing (newest years
count the most).
"""
from __future__ import annotations

from typing import Any

from ky_core.storage import Repository

from ._loaders import (
    dps_history,
    fnguide_payloads,
    latest_close_map,
    universe_map,
    fnguide_get,
)

ARISTOCRAT_YEARS = 10
# DPS can be flat or epsilon-down from rounding; tolerate 1% dip.
FLAT_TOLERANCE = 0.99


def _streak(series: list[tuple[str, float]]) -> int:
    """Longest trailing run where ``dps[i] >= dps[i-1] * FLAT_TOLERANCE``."""
    if not series:
        return 0
    streak = 0
    prev: float | None = None
    for _pe, dps in series:
        if dps <= 0:
            streak = 0
            prev = None
            continue
        if prev is None or dps >= prev * FLAT_TOLERANCE:
            streak += 1
        else:
            streak = 1
        prev = dps
    return streak


def _cagr(series: list[tuple[str, float]], years: int) -> float | None:
    """DPS CAGR over trailing ``years`` (needs ≥years+1 points)."""
    positives = [x for x in series if x[1] > 0]
    if len(positives) < years + 1:
        return None
    start = positives[-(years + 1)][1]
    end = positives[-1][1]
    if start <= 0:
        return None
    try:
        return (end / start) ** (1 / years) - 1
    except Exception:  # noqa: BLE001
        return None


def _dps_from_fnguide(payload: dict[str, Any] | None, price: float | None) -> float | None:
    """Fallback: DPS ≈ dividend_yield% × price. Returns None if either absent."""
    dy = fnguide_get(payload, "dividend_yield")
    if dy is None or price is None or price <= 0:
        return None
    return dy / 100.0 * price


def dps_for(
    symbol: str,
    *,
    repo: Repository | None = None,
    years: int = 10,
) -> dict[str, Any] | None:
    """Per-symbol DPS timeseries + aristocrat flag."""
    repo = repo or Repository()
    hist = dps_history(repo).get(symbol, [])
    series: list[tuple[str, float]] = [
        (r["period_end"], float(r["dps"]))
        for r in hist
        if r.get("dps") is not None and r.get("period_end")
    ]
    series.sort(key=lambda x: x[0])
    # Dedup on calendar year (DART sometimes files revisions).
    per_year: dict[str, float] = {}
    for pe, dps in series:
        year = pe[:4]
        per_year[year] = max(per_year.get(year, 0.0), dps)
    series = sorted(per_year.items())

    source = "dart"
    if not series:
        payload = fnguide_payloads(repo).get(symbol)
        price_row = latest_close_map(repo).get(symbol)
        price = price_row.get("close") if price_row else None
        est = _dps_from_fnguide(payload, price)
        if est is None:
            return None
        series = [(price_row["date"][:4] if price_row else "now", est)]
        source = "proxy:fnguide_yield"

    streak = _streak(series)
    cagr_5y = _cagr(series, 5)
    cagr_10y = _cagr(series, 10)
    aristocrat = streak >= ARISTOCRAT_YEARS and source == "dart"

    meta = universe_map(repo).get(symbol, {})
    latest = series[-1]
    return {
        "symbol": symbol,
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "market": meta.get("market"),
        "source": source,
        "years_reported": len(series),
        "latest_period": latest[0],
        "latest_dps": latest[1],
        "streak": streak,
        "aristocrat": aristocrat,
        "cagr_5y": cagr_5y,
        "cagr_10y": cagr_10y,
        "series": [{"period": pe, "dps": dps} for pe, dps in series[-years:]],
    }


def dps_scan(
    *,
    repo: Repository | None = None,
) -> list[dict[str, Any]]:
    """All symbols with any DPS history, sorted by streak desc then yield."""
    repo = repo or Repository()
    hist_map = dps_history(repo)
    meta_map = universe_map(repo)
    payloads = fnguide_payloads(repo)
    out: list[dict[str, Any]] = []
    for sym, hist in hist_map.items():
        per_year: dict[str, float] = {}
        for r in hist:
            pe = r.get("period_end") or ""
            dps = r.get("dps")
            if dps is None:
                continue
            year = pe[:4]
            per_year[year] = max(per_year.get(year, 0.0), float(dps))
        if not per_year:
            continue
        series = sorted(per_year.items())
        streak = _streak(series)
        meta = meta_map.get(sym, {})
        payload = payloads.get(sym)
        out.append(
            {
                "symbol": sym,
                "name": meta.get("name"),
                "sector": meta.get("sector"),
                "market": meta.get("market"),
                "years_reported": len(series),
                "latest_period": series[-1][0],
                "latest_dps": series[-1][1],
                "streak": streak,
                "aristocrat": streak >= ARISTOCRAT_YEARS,
                "cagr_5y": _cagr(series, 5),
                "cagr_10y": _cagr(series, 10),
                "dividend_yield": fnguide_get(payload, "dividend_yield"),
            }
        )
    out.sort(
        key=lambda r: (
            r["aristocrat"],
            r["streak"],
            r.get("cagr_5y") or 0.0,
            r.get("dividend_yield") or 0.0,
        ),
        reverse=True,
    )
    return out


def aristocrats(*, repo: Repository | None = None) -> list[dict[str, Any]]:
    return [r for r in dps_scan(repo=repo) if r["aristocrat"]]
