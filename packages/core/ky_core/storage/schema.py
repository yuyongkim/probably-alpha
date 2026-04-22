"""SQLAlchemy ORM schema for the ky-platform store.

Design notes:

- ``owner_id`` is present on every user-facing table so we can scope per-tenant
  reads/writes. Default: ``"self"``.
- ``Observation`` is the generic time-series row (macro series). ``series_id``
  is source-specific; (``source_id``, ``series_id``, ``date``, ``owner_id``) is
  the natural key.
- ``Filing`` mirrors OpenDART rows but generalises to any filing source.
- ``Universe`` is a stub for ticker metadata (populated once KIS is live).
- ``meta`` columns are JSON blobs for source-specific fields we don't want to
  promote to first-class columns.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# --------------------------------------------------------------------------- #
# Observations — macro time-series                                            #
# --------------------------------------------------------------------------- #


class Observation(Base):
    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "series_id", "date", "owner_id",
            name="uq_observations_src_series_date_owner",
        ),
        Index("ix_observations_source_series", "source_id", "series_id"),
        Index("ix_observations_date", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(32), nullable=False)
    series_id: Mapped[str] = mapped_column(String(128), nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False)  # ISO YYYY-MM-DD
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    owner_id: Mapped[str] = mapped_column(String(32), nullable=False, default="self")


# --------------------------------------------------------------------------- #
# Filings — DART disclosures                                                  #
# --------------------------------------------------------------------------- #


class Filing(Base):
    __tablename__ = "filings"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "receipt_no", "owner_id",
            name="uq_filings_src_receipt_owner",
        ),
        Index("ix_filings_corp_code", "corp_code"),
        Index("ix_filings_filed_at", "filed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(32), nullable=False)
    corp_code: Mapped[str] = mapped_column(String(32), nullable=False)
    receipt_no: Mapped[str] = mapped_column(String(32), nullable=False)
    filed_at: Mapped[str] = mapped_column(String(10), nullable=False)
    type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    owner_id: Mapped[str] = mapped_column(String(32), nullable=False, default="self")


# --------------------------------------------------------------------------- #
# Universe — ticker master (stub)                                             #
# --------------------------------------------------------------------------- #


class Universe(Base):
    __tablename__ = "universe"
    __table_args__ = (
        UniqueConstraint("ticker", "market", "owner_id", name="uq_universe_ticker_market_owner"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    market: Mapped[str] = mapped_column(String(16), nullable=False)  # KOSPI/KOSDAQ/NASDAQ/...
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    owner_id: Mapped[str] = mapped_column(String(32), nullable=False, default="self")
