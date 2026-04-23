"""Shared loaders for ky_core.value.derived modules.

All helpers here are side-effect-free readers against ky.db. They give
the downstream derived modules bulk, cached access to:

- 10-year annual balance-sheet rows per symbol (``pit_fy_rows``)
- Parsed fnguide snapshot payloads (``fnguide_payloads``)
- DART dividend history keyed by symbol (``dps_history``)
- Universe meta (name/sector/market)
- Latest close price per symbol

Each loader is memoised on the (repo.owner_id) key for the duration of
the process — value-derived scans typically run inside a single API
request so a 1-hour TTL is enough.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from typing import Any, Iterable

from sqlalchemy import text

from ky_core.storage import Repository

_CACHE_TTL_SEC = 3600.0
_CACHE: dict[str, tuple[float, Any]] = {}


def _cache_get(key: str) -> Any | None:
    hit = _CACHE.get(key)
    if not hit:
        return None
    if time.time() - hit[0] > _CACHE_TTL_SEC:
        return None
    return hit[1]


def _cache_put(key: str, value: Any) -> None:
    _CACHE[key] = (time.time(), value)


def clear_cache() -> None:
    _CACHE.clear()


# --------------------------------------------------------------------------- #
# financials_pit — annual rows with balance sheet                             #
# --------------------------------------------------------------------------- #


def pit_fy_rows(
    repo: Repository,
    *,
    min_years: int = 1,
    require_balance_sheet: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    """Return ``{symbol: [row, row...]}`` sorted by period_end ASC (oldest first).

    Each row has: ``period_end, revenue, operating_income, net_income,
    total_assets, total_equity, total_liabilities``.

    ``require_balance_sheet`` → drops rows where ``total_assets`` is NULL
    (Naver-style P&L-only rows). We always filter to ``period_type='FY'``.
    """
    cache_key = f"pit_fy|{repo.owner_id}|bs={int(require_balance_sheet)}|min={min_years}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    where = ["owner_id = :oid", "period_type = 'FY'"]
    if require_balance_sheet:
        where.append("total_assets IS NOT NULL")
    q = text(
        f"""
        SELECT symbol, period_end, revenue, operating_income, net_income,
               total_assets, total_equity, total_liabilities
        FROM financials_pit
        WHERE {' AND '.join(where)}
        ORDER BY symbol ASC, period_end ASC
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sym, period_end, rev, op, ni, ta, te, tl in rows:
        grouped[sym].append(
            {
                "period_end": period_end,
                "revenue": rev,
                "operating_income": op,
                "net_income": ni,
                "total_assets": ta,
                "total_equity": te,
                "total_liabilities": tl,
            }
        )
    # Dedup duplicate period_end rows (pit has both FY from naver + platform).
    cleaned: dict[str, list[dict[str, Any]]] = {}
    for sym, periods in grouped.items():
        seen: set[str] = set()
        dedup: list[dict[str, Any]] = []
        for p in periods:
            pe = p["period_end"]
            if pe in seen:
                continue
            seen.add(pe)
            dedup.append(p)
        if len(dedup) >= min_years:
            cleaned[sym] = dedup
    _cache_put(cache_key, cleaned)
    return cleaned


# --------------------------------------------------------------------------- #
# fnguide snapshots                                                           #
# --------------------------------------------------------------------------- #


def fnguide_payloads(repo: Repository) -> dict[str, dict[str, Any]]:
    """Parsed fnguide ``payload`` JSON keyed by symbol."""
    cache_key = f"fnguide|{repo.owner_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    q = text(
        """
        SELECT symbol, payload, fetched_at
        FROM fnguide_snapshots
        WHERE owner_id = :oid
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()
    out: dict[str, dict[str, Any]] = {}
    for sym, payload, fetched_at in rows:
        if not payload:
            continue
        try:
            p = json.loads(payload)
        except Exception:  # noqa: BLE001
            continue
        p["_fetched_at"] = fetched_at
        out[sym] = p
    _cache_put(cache_key, out)
    return out


# --------------------------------------------------------------------------- #
# dividend_history (DART)                                                     #
# --------------------------------------------------------------------------- #


def dps_history(repo: Repository) -> dict[str, list[dict[str, Any]]]:
    """``{symbol: [rows]}`` sorted ASC by period_end; common share_type only.

    ``share_type`` 'common' is the main record (preferred share has its own
    rows). DART splits rows per share_type and sometimes per report revision;
    we dedupe on (period_end, dps).
    """
    cache_key = f"dps_history|{repo.owner_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    rows = repo.get_all_dividend_history()
    by_sym: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r.get("dps") is None:
            continue
        by_sym[r["symbol"]].append(r)
    # Dedup on period_end (keep highest dps — revisions usually increase).
    for sym, lst in by_sym.items():
        best_per_period: dict[str, dict[str, Any]] = {}
        for row in lst:
            pe = row.get("period_end") or ""
            prev = best_per_period.get(pe)
            if prev is None or (row.get("dps") or 0) > (prev.get("dps") or 0):
                best_per_period[pe] = row
        by_sym[sym] = sorted(best_per_period.values(), key=lambda x: x.get("period_end") or "")
    out = dict(by_sym)
    _cache_put(cache_key, out)
    return out


# --------------------------------------------------------------------------- #
# universe meta                                                               #
# --------------------------------------------------------------------------- #


def universe_map(repo: Repository, symbols: Iterable[str] | None = None) -> dict[str, dict[str, Any]]:
    """``{ticker: {name, sector, market, industry}}`` — optionally filtered."""
    cache_key = f"universe|{repo.owner_id}"
    cached = _cache_get(cache_key)
    if cached is None:
        q = text(
            """
            SELECT ticker, name, sector, market, industry
            FROM universe
            WHERE owner_id = :oid
            """
        )
        with repo.session() as sess:
            rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()
        cached = {
            t: {"name": n, "sector": s, "market": m, "industry": ind}
            for t, n, s, m, ind in rows
        }
        _cache_put(cache_key, cached)
    if symbols is None:
        return cached
    wanted = set(symbols)
    return {t: v for t, v in cached.items() if t in wanted}


# --------------------------------------------------------------------------- #
# latest ohlcv close                                                          #
# --------------------------------------------------------------------------- #


def latest_close_map(repo: Repository) -> dict[str, dict[str, Any]]:
    """Latest (date, close) per symbol. One SQL pass over ``ohlcv``."""
    cache_key = f"latest_close|{repo.owner_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    q = text(
        """
        SELECT o.symbol, o.date, o.close
        FROM ohlcv o
        JOIN (
            SELECT symbol, MAX(date) AS max_date
            FROM ohlcv
            WHERE owner_id = :oid
            GROUP BY symbol
        ) latest
        ON o.symbol = latest.symbol AND o.date = latest.max_date
        WHERE o.owner_id = :oid
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()
    out = {sym: {"date": d, "close": float(c) if c is not None else None} for sym, d, c in rows}
    _cache_put(cache_key, out)
    return out


# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #


def safe_div(num: Any, den: Any) -> float | None:
    if num is None or den in (None, 0):
        return None
    try:
        return num / den
    except (ZeroDivisionError, TypeError):
        return None


def cagr(start: float | None, end: float | None, years: int) -> float | None:
    if start is None or end is None or start <= 0 or end <= 0 or years <= 0:
        return None
    try:
        return (end / start) ** (1 / years) - 1
    except Exception:  # noqa: BLE001
        return None


def fnguide_get(payload: dict[str, Any] | None, key: str) -> Any:
    if not payload:
        return None
    v = payload.get(key)
    try:
        if v is None:
            return None
        return float(v)
    except (TypeError, ValueError):
        return v
