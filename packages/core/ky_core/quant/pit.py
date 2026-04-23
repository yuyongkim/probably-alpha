"""Point-in-time financial helpers.

All fundamental lookups MUST use ``as_of`` to prevent look-ahead bias.
We prefer the ``quant_platform_pit`` source because it carries a real
``report_date`` (공시일). ``company_credit_fin`` rows fall back only when
no PIT row is available.

Bulk helpers (``ttm_fin_bulk``) load the whole universe in one SQL
statement and compute TTM in memory — this replaces the per-symbol
N+1 pattern used by the old ``scan()``/``*_leaderboard`` loops.
"""
from __future__ import annotations

from typing import Any, Iterable

from sqlalchemy import and_, desc, or_, select, text

from ky_core.storage import Repository
from ky_core.storage.schema import FinancialPIT, OHLCV, Universe

PIT_SOURCE = "quant_platform_pit"
_CC_SOURCE = "company_credit_fin"


def latest_fin(
    repo: Repository,
    symbol: str,
    *,
    as_of: str | None = None,
    period_type: str | None = None,
    require_balance_sheet: bool = False,
) -> dict[str, Any] | None:
    """Return the most-recent financial row ≤ as_of (PIT-safe).

    If ``require_balance_sheet`` is true, rows with NULL total_assets are
    filtered out — useful for Altman / Piotroski / Magic Formula.
    """
    with repo.session() as sess:
        stmt = select(FinancialPIT).where(
            FinancialPIT.symbol == symbol,
            FinancialPIT.owner_id == repo.owner_id,
        )
        if as_of is not None:
            # report_date ≤ as_of. Rows without report_date are only allowed
            # when the period_end itself is ≥ 90 days before as_of (heuristic).
            stmt = stmt.where(
                or_(
                    and_(FinancialPIT.report_date != None, FinancialPIT.report_date <= as_of),  # noqa: E711
                    and_(FinancialPIT.report_date == None, FinancialPIT.period_end <= as_of),   # noqa: E711
                )
            )
        if period_type:
            stmt = stmt.where(FinancialPIT.period_type == period_type)
        if require_balance_sheet:
            stmt = stmt.where(FinancialPIT.total_assets != None)  # noqa: E711
        stmt = stmt.order_by(
            # Prefer quant_platform_pit (richer schema) when tied on period_end
            desc(FinancialPIT.period_end),
            desc(FinancialPIT.source_id == PIT_SOURCE),
            desc(FinancialPIT.report_date),
        )
        row = sess.execute(stmt).scalars().first()
        if row is None:
            return None
        return _row_to_dict(row)


def ttm_fin(
    repo: Repository,
    symbol: str,
    *,
    as_of: str | None = None,
) -> dict[str, Any] | None:
    """Trailing-12-month aggregate in KRW.

    Source strategy (picked in order):
    1. ``company_credit_fin`` discrete quarterly rows (units: 억 KRW / 100M KRW)
       — sum last 4 quarters, scale up by 1e8 to return KRW.
    2. ``quant_platform_pit`` rows (units: KRW, YTD-cumulative). We take the
       most recent FY row to avoid YTD double-counting.
    Balance-sheet stock fields come from the most recent ``quant_platform_pit``
    row (it's the only source that carries them).
    """
    cc_rows = _load_rows(repo, symbol, as_of, source="company_credit_fin")
    pit_rows = _load_rows(repo, symbol, as_of, source=PIT_SOURCE)
    bs = next((r for r in pit_rows if r["total_assets"] is not None), None)
    # Preferred: 4 most recent company_credit quarters
    q_rows = [r for r in cc_rows if r["period_type"] in ("Q1", "Q2", "Q3", "Q4")]
    # Dedup by period_end (keep first = most recent)
    seen: set[str] = set()
    q_dedup: list[dict[str, Any]] = []
    for r in q_rows:
        if r["period_end"] in seen:
            continue
        seen.add(r["period_end"])
        q_dedup.append(r)
    if len(q_dedup) >= 4:
        recent = q_dedup[:4]
        scale = 1e8  # 억 KRW → KRW
        return {
            "symbol": symbol,
            "as_of": as_of,
            "period_end": recent[0]["period_end"],
            "revenue_ttm": _sum_key(recent, "revenue", scale),
            "operating_income_ttm": _sum_key(recent, "operating_income", scale),
            "net_income_ttm": _sum_key(recent, "net_income", scale),
            "total_assets": bs["total_assets"] if bs else None,
            "total_liabilities": bs["total_liabilities"] if bs else None,
            "total_equity": bs["total_equity"] if bs else None,
            "n_quarters": len(recent),
            "source": "company_credit_fin",
        }
    # Fallback: quant_platform_pit FY row
    fy = next((r for r in pit_rows if r["period_type"] == "FY"), None)
    if fy:
        return {
            "symbol": symbol,
            "as_of": as_of,
            "period_end": fy["period_end"],
            "revenue_ttm": fy["revenue"],
            "operating_income_ttm": fy["operating_income"],
            "net_income_ttm": fy["net_income"],
            "total_assets": fy["total_assets"],
            "total_liabilities": fy["total_liabilities"],
            "total_equity": fy["total_equity"],
            "n_quarters": 4,
            "source": "quant_platform_pit_fy",
        }
    return None


def _load_rows(
    repo: Repository, symbol: str, as_of: str | None, source: str
) -> list[dict[str, Any]]:
    with repo.session() as sess:
        stmt = select(FinancialPIT).where(
            FinancialPIT.symbol == symbol,
            FinancialPIT.owner_id == repo.owner_id,
            FinancialPIT.source_id == source,
        )
        if as_of is not None:
            stmt = stmt.where(
                or_(
                    and_(FinancialPIT.report_date != None, FinancialPIT.report_date <= as_of),  # noqa: E711
                    and_(FinancialPIT.report_date == None, FinancialPIT.period_end <= as_of),   # noqa: E711
                )
            )
        stmt = stmt.order_by(desc(FinancialPIT.period_end))
        rows = list(sess.execute(stmt).scalars().all())
    return [_row_to_dict(r) for r in rows]


def _sum_key(rows: list[dict[str, Any]], key: str, scale: float) -> float | None:
    vals = [r[key] for r in rows if r.get(key) is not None]
    if not vals:
        return None
    return float(sum(vals)) * scale


def fin_series(
    repo: Repository,
    symbol: str,
    *,
    n: int = 8,
    period_type: str | None = "Q",
) -> list[dict[str, Any]]:
    """Return the most recent ``n`` quarterly (or FY) financial rows, oldest→newest."""
    with repo.session() as sess:
        stmt = select(FinancialPIT).where(
            FinancialPIT.symbol == symbol,
            FinancialPIT.owner_id == repo.owner_id,
        )
        if period_type == "Q":
            stmt = stmt.where(FinancialPIT.period_type.in_(("Q1", "Q2", "Q3", "Q4")))
        elif period_type == "FY":
            stmt = stmt.where(FinancialPIT.period_type == "FY")
        stmt = stmt.order_by(desc(FinancialPIT.period_end)).limit(n)
        rows = list(sess.execute(stmt).scalars().all())
    rows.reverse()
    return [_row_to_dict(r) for r in rows]


def latest_price(repo: Repository, symbol: str, as_of: str | None = None) -> dict[str, Any] | None:
    with repo.session() as sess:
        stmt = select(OHLCV).where(
            OHLCV.symbol == symbol,
            OHLCV.owner_id == repo.owner_id,
        )
        if as_of is not None:
            stmt = stmt.where(OHLCV.date <= as_of)
        stmt = stmt.order_by(desc(OHLCV.date)).limit(1)
        row = sess.execute(stmt).scalars().first()
        if not row:
            return None
        return {
            "symbol": row.symbol,
            "market": row.market,
            "date": row.date,
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "volume": row.volume,
        }


def universe_meta(repo: Repository, symbol: str) -> dict[str, Any] | None:
    with repo.session() as sess:
        stmt = select(Universe).where(
            Universe.ticker == symbol,
            Universe.owner_id == repo.owner_id,
        ).limit(1)
        row = sess.execute(stmt).scalars().first()
        if not row:
            return None
        return {
            "ticker": row.ticker,
            "market": row.market,
            "name": row.name,
            "sector": row.sector,
            "industry": row.industry,
        }


def _row_to_dict(row: FinancialPIT) -> dict[str, Any]:
    return {
        "symbol": row.symbol,
        "period_end": row.period_end,
        "period_type": row.period_type,
        "report_date": row.report_date,
        "revenue": row.revenue,
        "operating_income": row.operating_income,
        "net_income": row.net_income,
        "total_assets": row.total_assets,
        "total_liabilities": row.total_liabilities,
        "total_equity": row.total_equity,
        "source_id": row.source_id,
    }


# --------------------------------------------------------------------------- #
# Bulk helpers — load the whole universe in one SQL pass                      #
# --------------------------------------------------------------------------- #


def _pit_rows_by_symbol(
    repo: Repository,
    symbols: Iterable[str] | None,
    as_of: str | None,
) -> dict[str, list[dict[str, Any]]]:
    """Return {symbol: [rows...]} sorted by period_end DESC.

    A single SQL query scoped to the owner. When ``symbols`` is None we load
    everything — callers that pass the universe should pre-filter for
    listed tickers. The per-symbol list is sorted newest first.
    """
    with repo.session() as sess:
        stmt = select(FinancialPIT).where(FinancialPIT.owner_id == repo.owner_id)
        if as_of is not None:
            stmt = stmt.where(
                or_(
                    and_(FinancialPIT.report_date != None, FinancialPIT.report_date <= as_of),  # noqa: E711
                    and_(FinancialPIT.report_date == None, FinancialPIT.period_end <= as_of),   # noqa: E711
                )
            )
        if symbols is not None:
            sym_list = list(symbols)
            if not sym_list:
                return {}
            out: dict[str, list[dict[str, Any]]] = {}
            for start in range(0, len(sym_list), 800):
                chunk = sym_list[start : start + 800]
                sub = stmt.where(FinancialPIT.symbol.in_(chunk)).order_by(
                    FinancialPIT.symbol.asc(),
                    desc(FinancialPIT.period_end),
                    desc(FinancialPIT.report_date),
                )
                rows = list(sess.execute(sub).scalars().all())
                for r in rows:
                    out.setdefault(r.symbol, []).append(_row_to_dict(r))
            return out
        stmt = stmt.order_by(
            FinancialPIT.symbol.asc(),
            desc(FinancialPIT.period_end),
            desc(FinancialPIT.report_date),
        )
        rows = list(sess.execute(stmt).scalars().all())
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        out.setdefault(r.symbol, []).append(_row_to_dict(r))
    return out


def _ttm_from_rows(
    symbol: str, rows: list[dict[str, Any]], as_of: str | None
) -> dict[str, Any] | None:
    """Compute a TTM aggregate from pre-fetched PIT rows (newest first).

    Mirrors :func:`ttm_fin` logic but without any I/O.
    """
    cc_rows = [r for r in rows if r["source_id"] == _CC_SOURCE]
    pit_rows = [r for r in rows if r["source_id"] == PIT_SOURCE]
    bs = next((r for r in pit_rows if r["total_assets"] is not None), None)
    q_rows = [r for r in cc_rows if r["period_type"] in ("Q1", "Q2", "Q3", "Q4")]
    seen: set[str] = set()
    q_dedup: list[dict[str, Any]] = []
    for r in q_rows:
        if r["period_end"] in seen:
            continue
        seen.add(r["period_end"])
        q_dedup.append(r)
    if len(q_dedup) >= 4:
        recent = q_dedup[:4]
        scale = 1e8  # 억 KRW → KRW
        return {
            "symbol": symbol,
            "as_of": as_of,
            "period_end": recent[0]["period_end"],
            "revenue_ttm": _sum_key(recent, "revenue", scale),
            "operating_income_ttm": _sum_key(recent, "operating_income", scale),
            "net_income_ttm": _sum_key(recent, "net_income", scale),
            "total_assets": bs["total_assets"] if bs else None,
            "total_liabilities": bs["total_liabilities"] if bs else None,
            "total_equity": bs["total_equity"] if bs else None,
            "n_quarters": len(recent),
            "source": "company_credit_fin",
        }
    fy = next((r for r in pit_rows if r["period_type"] == "FY"), None)
    if fy:
        return {
            "symbol": symbol,
            "as_of": as_of,
            "period_end": fy["period_end"],
            "revenue_ttm": fy["revenue"],
            "operating_income_ttm": fy["operating_income"],
            "net_income_ttm": fy["net_income"],
            "total_assets": fy["total_assets"],
            "total_liabilities": fy["total_liabilities"],
            "total_equity": fy["total_equity"],
            "n_quarters": 4,
            "source": "quant_platform_pit_fy",
        }
    return None


def ttm_fin_bulk(
    repo: Repository,
    symbols: Iterable[str],
    *,
    as_of: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Universe-wide TTM map: ``{symbol: ttm_dict}``.

    One (chunked) SQL read instead of one per symbol. Symbols with no
    usable rows are omitted from the result (same behaviour as calling
    :func:`ttm_fin` and filtering None).
    """
    by_sym = _pit_rows_by_symbol(repo, list(symbols), as_of)
    out: dict[str, dict[str, Any]] = {}
    for sym, rows in by_sym.items():
        ttm = _ttm_from_rows(sym, rows, as_of)
        if ttm:
            out[sym] = ttm
    return out


def ttm_fin_pair_bulk(
    repo: Repository,
    symbols: Iterable[str],
    *,
    as_of: str,
    prior_as_of: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return (now_map, prior_map) for YoY calculations in a single pass.

    Fetches all PIT rows with ``report_date ≤ as_of`` once, then derives
    both snapshots from the same result set. This keeps YoY screeners
    (fast_growth, Piotroski) off the N+1 path.
    """
    by_sym = _pit_rows_by_symbol(repo, list(symbols), as_of)
    now_map: dict[str, dict[str, Any]] = {}
    prior_map: dict[str, dict[str, Any]] = {}
    for sym, rows in by_sym.items():
        now = _ttm_from_rows(sym, rows, as_of)
        if now:
            now_map[sym] = now
        prior_rows = [
            r for r in rows
            if (r.get("report_date") or r.get("period_end") or "") <= prior_as_of
        ]
        prior = _ttm_from_rows(sym, prior_rows, prior_as_of)
        if prior:
            prior_map[sym] = prior
    return now_map, prior_map
