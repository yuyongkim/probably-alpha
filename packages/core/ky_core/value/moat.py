"""Economic-moat classifier — 10-year ROIC stability + level.

Morningstar-style moat rating from quantitative signals alone:

    - ROIC level      — 10-year average ROIC (proxy: operating income × (1 − tax)
                        / invested capital where invested = total equity + total
                        liabilities).
    - ROIC stability  — std dev of the 10-year ROIC series.
    - ROE consistency — supplementary: years with ROE > 10%.
    - Growth          — revenue CAGR over the window.

Classification:

    Wide   — 10y avg ROIC ≥ 15% AND std ≤ 5pp AND ROE>10% in ≥7/10 years.
    Narrow — 10y avg ROIC ≥ 10% AND std ≤ 8pp.
    None   — everything else.

Data source: ``financials_pit`` (annual, ``period_type='FY'``) — that's where
Korean balance sheet + P&L rows live together. Old versions of this file tried
the Naver per-account ``financial_statements_db``, but that store is P&L-only
(no equity / liabilities) so ROIC can't be computed there.
"""
from __future__ import annotations

import logging
import math
import time
from collections import defaultdict
from typing import Any

from sqlalchemy import text

from ky_core.storage import Repository

log = logging.getLogger(__name__)

_CACHE_TTL_SEC = 3600.0
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}

TAX_RATE = 0.22


def _pull_annual_rows(
    repo: Repository,
    *,
    min_years: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    """Bulk-load ``FY`` rows grouped by symbol, newest-first."""
    q = text(
        """
        SELECT symbol, period_end, revenue, operating_income, net_income,
               total_assets, total_equity, total_liabilities
        FROM financials_pit
        WHERE owner_id = :oid
          AND period_type = 'FY'
          AND total_equity IS NOT NULL
          AND operating_income IS NOT NULL
        ORDER BY symbol ASC, period_end ASC
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sym, period_end, rev, op, ni, assets, equity, liab in rows:
        grouped[sym].append(
            {
                "period_end": period_end,
                "revenue": rev,
                "operating_income": op,
                "net_income": ni,
                "total_assets": assets,
                "total_equity": equity,
                "total_liabilities": liab,
            }
        )
    return {sym: periods for sym, periods in grouped.items() if len(periods) >= min_years}


def _period_roic(row: dict[str, Any]) -> float | None:
    op = row.get("operating_income")
    eq = row.get("total_equity")
    liab = row.get("total_liabilities") or 0.0
    if op is None or eq is None:
        return None
    invested = eq + liab
    if invested <= 0:
        return None
    return op * (1 - TAX_RATE) / invested


def _period_roe(row: dict[str, Any]) -> float | None:
    ni = row.get("net_income")
    eq = row.get("total_equity")
    if ni is None or not eq or eq <= 0:
        return None
    return ni / eq


def _series_stats(series: list[float]) -> dict[str, float]:
    if not series:
        return {"mean": 0.0, "std": 0.0}
    n = len(series)
    mean = sum(series) / n
    var = sum((x - mean) ** 2 for x in series) / max(n - 1, 1)
    return {"mean": mean, "std": math.sqrt(var)}


def _revenue_cagr(periods: list[dict[str, Any]]) -> float | None:
    revs = [p["revenue"] for p in periods if p.get("revenue") and p["revenue"] > 0]
    if len(revs) < 2:
        return None
    first = revs[0]
    last = revs[-1]
    years = max(len(revs) - 1, 1)
    if first <= 0 or last <= 0:
        return None
    try:
        return (last / first) ** (1 / years) - 1
    except Exception:  # noqa: BLE001
        return None


def _classify(mean_roic: float, std_roic: float, roe_years: int, year_count: int) -> str:
    if year_count == 0:
        return "none"
    roe_share = roe_years / year_count
    if mean_roic >= 0.15 and std_roic <= 0.05 and roe_share >= 0.7:
        return "wide"
    if mean_roic >= 0.10 and std_roic <= 0.08:
        return "narrow"
    return "none"


def _load_meta(repo: Repository, symbols: list[str]) -> dict[str, dict[str, Any]]:
    universe: dict[str, dict[str, Any]] = {}
    for chunk_start in range(0, len(symbols), 500):
        chunk = symbols[chunk_start : chunk_start + 500]
        placeholders = ",".join([f":s{i}" for i in range(len(chunk))])
        params: dict[str, Any] = {f"s{i}": s for i, s in enumerate(chunk)}
        params["oid"] = repo.owner_id
        q = text(
            f"""
            SELECT ticker, name, sector, market
            FROM universe
            WHERE owner_id = :oid
              AND ticker IN ({placeholders})
            """
        )
        with repo.session() as sess:
            rows = sess.execute(q, params).fetchall()
        for t, name, sector, market in rows:
            universe[t] = {"name": name, "sector": sector, "market": market}
    return universe


def moat_scan(
    *,
    repo: Repository | None = None,
    min_years: int = 5,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Classify every symbol with ≥ ``min_years`` annual financials."""
    cache_key = f"moat|min_years={min_years}"
    if use_cache:
        hit = _CACHE.get(cache_key)
        if hit and time.time() - hit[0] <= _CACHE_TTL_SEC:
            return hit[1]

    repo = repo or Repository()
    grouped = _pull_annual_rows(repo, min_years=min_years)
    if not grouped:
        return []

    universe = _load_meta(repo, list(grouped.keys()))

    out: list[dict[str, Any]] = []
    for sym, periods in grouped.items():
        # Take the most recent 10 years.
        recent = periods[-10:]
        roic_series: list[float] = []
        roe_series: list[float] = []
        for p in recent:
            r = _period_roic(p)
            if r is not None:
                roic_series.append(r)
            roe = _period_roe(p)
            if roe is not None:
                roe_series.append(roe)
        if len(roic_series) < min_years:
            continue
        stats = _series_stats(roic_series)
        roe_years = sum(1 for x in roe_series if x > 0.10)
        label = _classify(stats["mean"], stats["std"], roe_years, len(roic_series))
        cagr = _revenue_cagr(recent)
        meta = universe.get(sym, {})
        out.append(
            {
                "symbol": sym,
                "name": meta.get("name"),
                "sector": meta.get("sector"),
                "market": meta.get("market"),
                "roic_10y_mean": stats["mean"],
                "roic_10y_std": stats["std"],
                "roe_years_above_10pct": roe_years,
                "years_used": len(roic_series),
                "revenue_cagr": cagr,
                "moat": label,
            }
        )

    out.sort(
        key=lambda r: (
            0 if r["moat"] == "wide" else 1 if r["moat"] == "narrow" else 2,
            -(r["roic_10y_mean"] or 0),
        )
    )

    if use_cache:
        _CACHE[cache_key] = (time.time(), out)
    return out


def moat_summary(
    *,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    rows = moat_scan(repo=repo, use_cache=use_cache)
    kpi = {
        "total": len(rows),
        "wide": sum(1 for r in rows if r["moat"] == "wide"),
        "narrow": sum(1 for r in rows if r["moat"] == "narrow"),
        "none": sum(1 for r in rows if r["moat"] == "none"),
    }
    return {"kpi": kpi, "rows": [r for r in rows if r["moat"] in ("wide", "narrow")][:100]}
