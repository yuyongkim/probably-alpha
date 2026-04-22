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
from ky_core.storage.schema import Filing, Observation, Universe


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
                "meta": stmt.excluded.meta,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        with self.session() as sess:
            sess.execute(stmt)
        return len(payload)


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
