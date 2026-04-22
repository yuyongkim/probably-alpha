"""Repository — thin CRUD wrapper around the SQLAlchemy schema.

Why a wrapper: application code and collect scripts should not construct ORM
sessions or execute raw SQL. They pass dicts shaped like the adapter rows and
the repository takes care of upserting, dedup, and tenant scoping.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable, Iterator, Sequence

from sqlalchemy import and_, desc, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from ky_core.storage.db import get_session_factory, init_db
from ky_core.storage.schema import Filing, FinancialPIT, Observation, OHLCV, Universe


class Repository:
    """Entry point for all persistence operations."""

    def __init__(self, owner_id: str = "self", *, auto_init: bool = True) -> None:
        self.owner_id = owner_id
        if auto_init:
            init_db()

    # --------- Session management ---------

    @contextmanager
    def session(self) -> Iterator[Session]:
        factory = get_session_factory()
        sess = factory()
        try:
            yield sess
            sess.commit()
        except Exception:
            sess.rollback()
            raise
        finally:
            sess.close()

    # --------- Observations ---------

    def upsert_observations(self, rows: Iterable[dict[str, Any]]) -> int:
        """Upsert observation rows. Returns the number of rows written."""
        rows = list(rows)
        if not rows:
            return 0
        now = datetime.utcnow()
        payload = []
        for row in rows:
            payload.append(
                {
                    "source_id": row["source_id"],
                    "series_id": row["series_id"],
                    "date": row["date"],
                    "value": row.get("value"),
                    "unit": row.get("unit"),
                    "meta": row.get("meta"),
                    "fetched_at": now,
                    "owner_id": row.get("owner_id", self.owner_id),
                }
            )
        stmt = sqlite_insert(Observation.__table__).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_id", "series_id", "date", "owner_id"],
            set_={
                "value": stmt.excluded.value,
                "unit": stmt.excluded.unit,
                "meta": stmt.excluded.meta,
                "fetched_at": stmt.excluded.fetched_at,
            },
        )
        with self.session() as sess:
            sess.execute(stmt)
        return len(payload)

    def get_observations(
        self,
        source_id: str,
        series_id: str,
        start: str | None = None,
        end: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        with self.session() as sess:
            stmt = select(Observation).where(
                and_(
                    Observation.source_id == source_id,
                    Observation.series_id == series_id,
                    Observation.owner_id == self.owner_id,
                )
            )
            if start:
                stmt = stmt.where(Observation.date >= start)
            if end:
                stmt = stmt.where(Observation.date <= end)
            stmt = stmt.order_by(Observation.date.asc())
            if limit:
                stmt = stmt.limit(limit)
            rows = sess.execute(stmt).scalars().all()
            return [_obs_to_dict(r) for r in rows]

    def latest_observation(self, source_id: str, series_id: str) -> dict[str, Any] | None:
        with self.session() as sess:
            stmt = (
                select(Observation)
                .where(
                    Observation.source_id == source_id,
                    Observation.series_id == series_id,
                    Observation.owner_id == self.owner_id,
                )
                .order_by(desc(Observation.date))
                .limit(1)
            )
            row = sess.execute(stmt).scalars().first()
            return _obs_to_dict(row) if row else None

    # --------- Filings ---------

    def upsert_filings(self, rows: Iterable[dict[str, Any]]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        now = datetime.utcnow()
        payload = []
        for row in rows:
            payload.append(
                {
                    "source_id": row["source_id"],
                    "corp_code": row.get("corp_code", ""),
                    "receipt_no": row["receipt_no"],
                    "filed_at": row.get("filed_at", ""),
                    "type": row.get("type"),
                    "summary": row.get("summary"),
                    "meta": row.get("meta"),
                    "fetched_at": now,
                    "owner_id": row.get("owner_id", self.owner_id),
                }
            )
        stmt = sqlite_insert(Filing.__table__).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_id", "receipt_no", "owner_id"],
            set_={
                "type": stmt.excluded.type,
                "summary": stmt.excluded.summary,
                "meta": stmt.excluded.meta,
                "filed_at": stmt.excluded.filed_at,
                "corp_code": stmt.excluded.corp_code,
                "fetched_at": stmt.excluded.fetched_at,
            },
        )
        with self.session() as sess:
            sess.execute(stmt)
        return len(payload)

    def recent_filings(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.session() as sess:
            stmt = (
                select(Filing)
                .where(Filing.owner_id == self.owner_id)
                .order_by(desc(Filing.filed_at))
                .limit(limit)
            )
            rows = sess.execute(stmt).scalars().all()
            return [_filing_to_dict(r) for r in rows]

    # --------- Universe ---------

    def upsert_universe(self, rows: Sequence[dict[str, Any]]) -> int:
        if not rows:
            return 0
        now = datetime.utcnow()
        payload = [
            {
                "ticker": r["ticker"],
                "market": r["market"],
                "name": r.get("name"),
                "sector": r.get("sector"),
                "industry": r.get("industry"),
                "is_etf": bool(r.get("is_etf", False)),
                "meta": r.get("meta"),
                "updated_at": now,
                "owner_id": r.get("owner_id", self.owner_id),
            }
            for r in rows
        ]
        stmt = sqlite_insert(Universe.__table__).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker", "market", "owner_id"],
            set_={
                "name": stmt.excluded.name,
                "sector": stmt.excluded.sector,
                "industry": stmt.excluded.industry,
                "is_etf": stmt.excluded.is_etf,
                "meta": stmt.excluded.meta,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        with self.session() as sess:
            sess.execute(stmt)
        return len(payload)

    def count_universe(self) -> int:
        with self.session() as sess:
            return sess.query(Universe).filter(Universe.owner_id == self.owner_id).count()

    def get_universe(self, ticker: str) -> dict[str, Any] | None:
        with self.session() as sess:
            stmt = (
                select(Universe)
                .where(Universe.ticker == ticker, Universe.owner_id == self.owner_id)
                .limit(1)
            )
            row = sess.execute(stmt).scalars().first()
            if not row:
                return None
            return {
                "ticker": row.ticker,
                "market": row.market,
                "name": row.name,
                "sector": row.sector,
                "industry": row.industry,
                "is_etf": bool(row.is_etf),
                "meta": row.meta,
            }

    # --------- OHLCV ---------

    def upsert_ohlcv(self, rows: Iterable[dict[str, Any]]) -> int:
        """Batch upsert OHLCV rows.

        Each row must contain: symbol, date (ISO), close, source_id.
        Optional: open, high, low, volume, adj_close, market, owner_id.
        """
        rows = list(rows)
        if not rows:
            return 0
        now = datetime.utcnow()
        payload = []
        for row in rows:
            payload.append(
                {
                    "symbol": row["symbol"],
                    "market": row.get("market") or "UNKNOWN",
                    "date": row["date"],
                    "open": row.get("open"),
                    "high": row.get("high"),
                    "low": row.get("low"),
                    "close": row["close"],
                    "volume": row.get("volume"),
                    "adj_close": row.get("adj_close"),
                    "source_id": row["source_id"],
                    "fetched_at": now,
                    "owner_id": row.get("owner_id", self.owner_id),
                }
            )
        stmt = sqlite_insert(OHLCV.__table__).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=["owner_id", "symbol", "date"],
            set_={
                "market": stmt.excluded.market,
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "adj_close": stmt.excluded.adj_close,
                "source_id": stmt.excluded.source_id,
                "fetched_at": stmt.excluded.fetched_at,
            },
        )
        with self.session() as sess:
            sess.execute(stmt)
        return len(payload)

    def get_ohlcv(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        with self.session() as sess:
            stmt = select(OHLCV).where(
                OHLCV.symbol == symbol,
                OHLCV.owner_id == self.owner_id,
            )
            if start:
                stmt = stmt.where(OHLCV.date >= start)
            if end:
                stmt = stmt.where(OHLCV.date <= end)
            stmt = stmt.order_by(OHLCV.date.asc())
            if limit:
                stmt = stmt.limit(limit)
            return [_ohlcv_to_dict(r) for r in sess.execute(stmt).scalars().all()]

    def get_ohlcv_latest(self, symbol: str) -> dict[str, Any] | None:
        with self.session() as sess:
            stmt = (
                select(OHLCV)
                .where(OHLCV.symbol == symbol, OHLCV.owner_id == self.owner_id)
                .order_by(desc(OHLCV.date))
                .limit(1)
            )
            row = sess.execute(stmt).scalars().first()
            return _ohlcv_to_dict(row) if row else None

    def count_ohlcv(self) -> int:
        with self.session() as sess:
            return sess.query(OHLCV).filter(OHLCV.owner_id == self.owner_id).count()

    def count_ohlcv_symbols(self) -> int:
        from sqlalchemy import distinct, func
        with self.session() as sess:
            return sess.query(func.count(distinct(OHLCV.symbol))).filter(
                OHLCV.owner_id == self.owner_id
            ).scalar() or 0

    # --------- Financials PIT ---------

    def upsert_financials(self, rows: Iterable[dict[str, Any]]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        now = datetime.utcnow()
        payload = []
        for row in rows:
            payload.append(
                {
                    "corp_code": row.get("corp_code"),
                    "symbol": row["symbol"],
                    "report_date": row.get("report_date"),
                    "period_end": row["period_end"],
                    "period_type": row["period_type"],
                    "revenue": row.get("revenue"),
                    "operating_income": row.get("operating_income"),
                    "net_income": row.get("net_income"),
                    "total_assets": row.get("total_assets"),
                    "total_liabilities": row.get("total_liabilities"),
                    "total_equity": row.get("total_equity"),
                    "raw": row.get("raw"),
                    "source_id": row["source_id"],
                    "fetched_at": now,
                    "owner_id": row.get("owner_id", self.owner_id),
                }
            )
        stmt = sqlite_insert(FinancialPIT.__table__).values(payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=["owner_id", "symbol", "period_end", "period_type", "source_id"],
            set_={
                "corp_code": stmt.excluded.corp_code,
                "report_date": stmt.excluded.report_date,
                "revenue": stmt.excluded.revenue,
                "operating_income": stmt.excluded.operating_income,
                "net_income": stmt.excluded.net_income,
                "total_assets": stmt.excluded.total_assets,
                "total_liabilities": stmt.excluded.total_liabilities,
                "total_equity": stmt.excluded.total_equity,
                "raw": stmt.excluded.raw,
                "fetched_at": stmt.excluded.fetched_at,
            },
        )
        with self.session() as sess:
            sess.execute(stmt)
        return len(payload)

    def get_financials(
        self,
        symbol: str,
        period_end: str | None = None,
        as_of: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return financials. If ``as_of`` provided, only those with
        report_date <= as_of (proper PIT query)."""
        with self.session() as sess:
            stmt = select(FinancialPIT).where(
                FinancialPIT.symbol == symbol,
                FinancialPIT.owner_id == self.owner_id,
            )
            if period_end:
                stmt = stmt.where(FinancialPIT.period_end == period_end)
            if as_of:
                stmt = stmt.where(FinancialPIT.report_date != None)  # noqa: E711
                stmt = stmt.where(FinancialPIT.report_date <= as_of)
            stmt = stmt.order_by(FinancialPIT.period_end.desc())
            return [_fin_to_dict(r) for r in sess.execute(stmt).scalars().all()]

    def count_financials(self) -> int:
        with self.session() as sess:
            return sess.query(FinancialPIT).filter(
                FinancialPIT.owner_id == self.owner_id
            ).count()


# --------------------------------------------------------------------------- #
# Row adapters                                                                #
# --------------------------------------------------------------------------- #


def _obs_to_dict(row: Observation) -> dict[str, Any]:
    return {
        "source_id": row.source_id,
        "series_id": row.series_id,
        "date": row.date,
        "value": row.value,
        "unit": row.unit,
        "meta": row.meta,
        "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
        "owner_id": row.owner_id,
    }


def _filing_to_dict(row: Filing) -> dict[str, Any]:
    return {
        "source_id": row.source_id,
        "corp_code": row.corp_code,
        "receipt_no": row.receipt_no,
        "filed_at": row.filed_at,
        "type": row.type,
        "summary": row.summary,
        "meta": row.meta,
        "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
        "owner_id": row.owner_id,
    }


def _ohlcv_to_dict(row: OHLCV) -> dict[str, Any]:
    return {
        "symbol": row.symbol,
        "market": row.market,
        "date": row.date,
        "open": row.open,
        "high": row.high,
        "low": row.low,
        "close": row.close,
        "volume": row.volume,
        "adj_close": row.adj_close,
        "source_id": row.source_id,
        "owner_id": row.owner_id,
    }


def _fin_to_dict(row: FinancialPIT) -> dict[str, Any]:
    return {
        "corp_code": row.corp_code,
        "symbol": row.symbol,
        "report_date": row.report_date,
        "period_end": row.period_end,
        "period_type": row.period_type,
        "revenue": row.revenue,
        "operating_income": row.operating_income,
        "net_income": row.net_income,
        "total_assets": row.total_assets,
        "total_liabilities": row.total_liabilities,
        "total_equity": row.total_equity,
        "raw": row.raw,
        "source_id": row.source_id,
        "owner_id": row.owner_id,
    }
