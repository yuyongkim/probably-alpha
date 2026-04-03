from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


DEFAULT_MAIN_DB = './data/quant_platform.db'
DEFAULT_BACKUP_DB = 'data/quant_platform_backup_before_split_20260308_220608.db'
DEFAULT_SNAPSHOT_SUFFIX = '_snapshot'
DEFAULT_HISTORY_SUFFIX = '_history'


@dataclass(frozen=True)
class QuantDbLayout:
    project_dir: Path
    main: Path | None
    snapshot: Path | None
    history: Path | None
    backup: Path | None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _project_dir_candidates() -> list[Path]:
    repo_root = _repo_root()
    candidates = [
        Path.home() / 'Desktop' / 'QuantDB' / 'mvp_platform',
        repo_root.parent / 'QuantDB' / 'mvp_platform',
    ]
    out: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def _resolve_with_project(raw: str, project_dir: Path) -> Path | None:
    value = str(raw or '').strip()
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return (project_dir / path).resolve()


def _derive_split_db_path(path: Path, suffix: str) -> Path:
    if path.suffix:
        return path.with_name(f'{path.stem}{suffix}{path.suffix}')
    return path.with_name(f'{path.name}{suffix}')


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "select 1 from sqlite_master where type='table' and name=? limit 1",
        (table,),
    ).fetchone()
    return bool(row)


def _path_has_any_tables(path: Path | None, tables: tuple[str, ...]) -> bool:
    if not path or not path.exists() or not path.is_file() or path.stat().st_size <= 0:
        return False
    try:
        with sqlite3.connect(path) as conn:
            return any(_table_exists(conn, table) for table in tables)
    except sqlite3.Error:
        return False


def _layout_candidates() -> list[QuantDbLayout]:
    env_main = str(os.getenv('SEPA_QUANTDB_PATH', '') or os.getenv('DB_PATH', '')).strip()
    env_snapshot = str(os.getenv('SNAPSHOT_DB_PATH', '')).strip()
    env_history = str(os.getenv('HISTORY_DB_PATH', '')).strip()

    out: list[QuantDbLayout] = []
    seen: set[tuple[str, str, str, str]] = set()

    for project_dir in _project_dir_candidates():
        main = _resolve_with_project(env_main or DEFAULT_MAIN_DB, project_dir)
        backup = _resolve_with_project(DEFAULT_BACKUP_DB, project_dir)
        snapshot = _resolve_with_project(env_snapshot, project_dir) if env_snapshot else (_derive_split_db_path(main, DEFAULT_SNAPSHOT_SUFFIX) if main else None)
        history = _resolve_with_project(env_history, project_dir) if env_history else (_derive_split_db_path(main, DEFAULT_HISTORY_SUFFIX) if main else None)
        key = (
            str(project_dir),
            str(main or ''),
            str(snapshot or ''),
            str(history or ''),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(QuantDbLayout(project_dir=project_dir, main=main, snapshot=snapshot, history=history, backup=backup))
    return out


@lru_cache(maxsize=1)
def resolve_quantdb_layout() -> QuantDbLayout | None:
    for layout in _layout_candidates():
        if _path_has_any_tables(layout.main, ('prices', 'tickers', 'quantking_snapshot')):
            return layout
        if _path_has_any_tables(layout.backup, ('prices', 'tickers', 'financials_quarterly')):
            return QuantDbLayout(
                project_dir=layout.project_dir,
                main=layout.backup,
                snapshot=layout.backup,
                history=layout.backup,
                backup=layout.backup,
            )
    return None


def resolve_quantdb_path() -> Path | None:
    layout = resolve_quantdb_layout()
    return layout.main if layout else None
