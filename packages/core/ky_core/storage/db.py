"""SQLAlchemy engine + session factory for the ky-platform SQLite store."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

DEFAULT_DB_PATH = Path.home() / ".ky-platform" / "data" / "ky.db"


def _resolve_db_path() -> Path:
    override = os.environ.get("KY_DB_PATH")
    path = Path(override) if override else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    path = _resolve_db_path()
    url = f"sqlite:///{path.as_posix()}"
    # NullPool: every session opens its own SQLite connection and closes on
    # disposal. SQLite handles many concurrent *readers* cheaply and the default
    # QueuePool (size=5, overflow=10) gets exhausted quickly when the API runs
    # parallel page requests that each hold a session for several seconds —
    # the FastAPI thread-pool can fan out to ~40 workers. NullPool avoids the
    # QueuePool exhaustion without hurting correctness on file-backed SQLite.
    engine = create_engine(
        url,
        future=True,
        echo=False,
        poolclass=NullPool,
        connect_args={"check_same_thread": False, "timeout": 30},
    )
    return engine


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False, future=True)


def init_db() -> None:
    """Create all tables if they don't exist."""
    from ky_core.storage.schema import Base  # local import to avoid cycles

    engine = get_engine()
    Base.metadata.create_all(engine)


def reset_engine_cache() -> None:
    """Test hook: clear memoised engine/session."""
    get_engine.cache_clear()
    get_session_factory.cache_clear()
