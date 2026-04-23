#!/usr/bin/env python
"""Bulk-import legacy macro archives into ky.db ``observations``.

This script pulls from the inventoried sources (see
``scripts/inventory_legacy_macro.py``) and writes to the existing
``observations`` table — it never creates a new table or changes schema.

Sources and the ``source_id`` tag each ends up with:

  ecos_legacy_qp        ECOS rows inside QuantPlatform category CSVs
  fred_legacy_qp        FRED rows inside QuantPlatform category CSVs
  kosis_legacy_qp       KOSIS rows inside QuantPlatform category CSVs
  commodity_legacy_qp   QuantPlatform commodities/*.csv (derived from filename)
  macro_legacy_qdb      QuantDB quant_platform_history.db::macro_series
  (+ eia_legacy_qdb, quantking_legacy_qdb for history.db rows)

De-duplication strategy
-----------------------
* Inside one source, the INSERT ... ON CONFLICT DO UPDATE keyed on
  (source_id, series_id, date, owner_id) keeps the last-seen value
  (which is the most recent source file via CSV mtime ordering).
* Across different source_ids the row lands under its own source_id so
  the same (series_id, date) can coexist with fresh adapter rows
  (e.g. ``ecos`` vs ``ecos_legacy_qp``). Macro Compass queries collapse
  across source_id via ``SELECT ... WHERE series_id = ?`` already.

Usage::

    python scripts/import_legacy_macro.py --dry-run
    python scripts/import_legacy_macro.py --source quantplatform_ecos
    python scripts/import_legacy_macro.py --source quantplatform_commodity
    python scripts/import_legacy_macro.py --source quantdb_history
    python scripts/import_legacy_macro.py --source all
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "packages" / "core", ROOT / "packages" / "adapters"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from ky_core.storage import init_db  # noqa: E402
from ky_core.storage.db import _resolve_db_path, reset_engine_cache  # noqa: E402
from ky_core.storage.presets import (  # noqa: E402
    LEGACY_SRC_COMMODITY,
    LEGACY_SRC_ECOS_QP,
    LEGACY_SRC_FRED_QP,
    LEGACY_SRC_KOSIS_QP,
    LEGACY_SRC_MACRO_DB,
    LEGACY_SRC_UNKNOWN,
    LEGACY_SOURCE_PREFIX_MAP,
)

LOG_DIR = ROOT / "runtime_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------- paths ------------------------------------------

QP_MACRO = Path("C:/Users/USER/Desktop/QuantPlatform/macro/data")
QP_ECOS_CATEGORIZED = QP_MACRO / "ecos" / "카테고리별_그룹화"
QP_COMMODITY = QP_MACRO / "commodities"
QDB_HISTORY_DB = Path(
    "C:/Users/USER/Desktop/QuantDB/mvp_platform/data/quant_platform_history.db"
)
ALIASES_YML = ROOT / "packages" / "core" / "ky_core" / "storage" / "series_aliases.yml"

BATCH_SIZE = 10_000
LOG_EVERY_ROWS = 50_000

# --------------------------- logging ----------------------------------------

log = logging.getLogger("import_legacy_macro")


def _setup_logging() -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"import_legacy_macro_{ts}.log"
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.handlers.clear()
    root.addHandler(fh)
    root.addHandler(sh)
    return log_path


# --------------------------- alias loading ----------------------------------


def _load_aliases() -> dict[str, dict[str, str]]:
    """Return {source_namespace: {name: canonical_id}}.

    We parse the YAML by hand rather than add a PyYAML dependency — the
    file format is constrained (one nested level, quoted string keys).
    """
    if not ALIASES_YML.exists():
        log.warning("aliases file missing: %s", ALIASES_YML)
        return {}
    out: dict[str, dict[str, str]] = defaultdict(dict)
    current: str | None = None
    for raw in ALIASES_YML.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            # top-level namespace like `ecos:`
            if line.endswith(":"):
                current = line[:-1].strip()
            continue
        if current is None:
            continue
        # expected form: `  "key": "value"`
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key = key.strip().strip('"').strip("'")
        val = val.strip().strip('"').strip("'")
        if key and val:
            out[current][key] = val
    return dict(out)


# --------------------------- normalization ----------------------------------


def _norm_date(v: Any) -> str | None:
    """Return ISO YYYY-MM-DD or None if junk."""
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() == "nan":
        return None
    # strip trailing time portion
    s = s.split(" ")[0].split("T")[0]
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    # YYYYMMDD fallback
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:]}"
    try:
        dt = pd.to_datetime(s, errors="coerce")
    except Exception:
        return None
    if pd.isna(dt):
        return None
    return dt.strftime("%Y-%m-%d")


def _norm_value(v: Any) -> float | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def _resolve_series_id(
    aliases: dict[str, dict[str, str]],
    namespace: str,
    indicator: str,
    fallback_native_id: str | None = None,
) -> str:
    """Look up canonical id; otherwise return native or ``legacy:<indicator>``."""
    if indicator:
        ns = aliases.get(namespace, {})
        if indicator in ns:
            return ns[indicator]
        # also check across namespaces — some FRED codes appear in ECOS files
        for other_ns, tbl in aliases.items():
            if other_ns == namespace:
                continue
            if indicator in tbl:
                return tbl[indicator]
    if fallback_native_id:
        return fallback_native_id
    return f"legacy:{indicator}" if indicator else "legacy:unknown"


def _clip_source_id(src: str) -> str:
    """Observation.source_id is VARCHAR(32)."""
    return src[:32]


# --------------------------- destination setup ------------------------------


def _open_dest() -> sqlite3.Connection:
    db_path = _resolve_db_path()
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA temp_store=MEMORY")
    con.execute("PRAGMA cache_size=-200000")
    con.execute("PRAGMA foreign_keys=OFF")
    return con


def _insert_stmt() -> str:
    return (
        "INSERT INTO observations "
        "(source_id, series_id, date, value, unit, meta, fetched_at, owner_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 'self') "
        "ON CONFLICT(source_id, series_id, date, owner_id) DO UPDATE SET "
        "  value=excluded.value, unit=excluded.unit, meta=excluded.meta,"
        "  fetched_at=excluded.fetched_at"
    )


class BatchWriter:
    """Buffer observation rows and flush in ``BATCH_SIZE`` chunks."""

    def __init__(
        self,
        con: sqlite3.Connection,
        *,
        dry_run: bool = False,
        tag: str = "",
    ) -> None:
        self.con = con
        self.dry_run = dry_run
        self.tag = tag
        self.buffer: list[tuple[Any, ...]] = []
        self.total_in = 0
        self.total_out = 0
        self.by_source: dict[str, int] = defaultdict(int)
        self.by_series: dict[tuple[str, str], int] = defaultdict(int)

    def add(
        self,
        *,
        source_id: str,
        series_id: str,
        date: str,
        value: float | None,
        unit: str | None,
        meta: dict[str, Any] | None,
    ) -> None:
        self.total_in += 1
        if value is None or not date:
            return
        source_id = _clip_source_id(source_id)
        series_id = series_id[:128]
        self.buffer.append(
            (
                source_id,
                series_id,
                date,
                value,
                unit[:64] if unit else None,
                json.dumps(meta, ensure_ascii=False) if meta else None,
                datetime.utcnow().isoformat(),
            )
        )
        self.by_source[source_id] += 1
        self.by_series[(source_id, series_id)] += 1
        if len(self.buffer) >= BATCH_SIZE:
            self.flush()

    def flush(self) -> None:
        if not self.buffer:
            return
        if self.dry_run:
            self.total_out += len(self.buffer)
            self.buffer.clear()
            return
        stmt = _insert_stmt()
        cur = self.con.cursor()
        cur.executemany(stmt, self.buffer)
        self.con.commit()
        self.total_out += len(self.buffer)
        self.buffer.clear()
        if self.total_out % LOG_EVERY_ROWS < BATCH_SIZE:
            log.info(
                "[%s] committed %s rows (in=%s)",
                self.tag,
                f"{self.total_out:,}",
                f"{self.total_in:,}",
            )


# --------------------------- source adapters --------------------------------


def _map_csv_source_to_source_id(src: str) -> str:
    s = (src or "").strip().upper()
    if s == "ECOS":
        return LEGACY_SRC_ECOS_QP
    if s in {"FRED", "FRED_PUBLIC"}:
        return LEGACY_SRC_FRED_QP
    if s == "KOSIS":
        return LEGACY_SRC_KOSIS_QP
    if s.startswith("PHASE4_FRED"):
        return LEGACY_SRC_FRED_QP
    return LEGACY_SRC_UNKNOWN


def _ingest_quantplatform_ecos(
    writer: BatchWriter,
    aliases: dict[str, dict[str, str]],
) -> None:
    """Pull from the 14 category CSV bundles (the superset file-set)."""
    if not QP_ECOS_CATEGORIZED.exists():
        log.warning("skip QP ECOS: %s missing", QP_ECOS_CATEGORIZED)
        return

    # Process files newest-mtime first so later rows overwrite older dupes
    files = sorted(
        QP_ECOS_CATEGORIZED.glob("*.csv"),
        key=lambda p: p.stat().st_mtime,
    )
    log.info("QP ECOS categorized: %s files", len(files))

    for path in files:
        try:
            df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
        except Exception as exc:
            log.error("read fail %s: %s", path.name, exc)
            continue
        required = {"date", "indicator", "value", "source"}
        if not required.issubset(df.columns):
            log.warning(
                "skip %s: missing columns %s", path.name, required - set(df.columns)
            )
            continue

        for row in df.itertuples(index=False):
            indicator = str(getattr(row, "indicator", "") or "")
            source_tag = str(getattr(row, "source", "") or "")
            source_id = _map_csv_source_to_source_id(source_tag)
            namespace = source_tag.strip().lower() if source_tag else "ecos"
            if namespace in {"fred_public", "phase4_fred"}:
                namespace = "fred"
            series_id = _resolve_series_id(
                aliases,
                namespace if namespace in aliases else "ecos",
                indicator,
            )
            writer.add(
                source_id=source_id,
                series_id=series_id,
                date=_norm_date(getattr(row, "date", None)) or "",
                value=_norm_value(getattr(row, "value", None)),
                unit=(
                    str(getattr(row, "unit", "") or "")[:64]
                    or None
                ),
                meta={
                    "legacy_source": "quantplatform_macro_ecos",
                    "legacy_indicator": indicator,
                    "legacy_source_tag": source_tag,
                    "legacy_file": path.name,
                    "category": str(getattr(row, "category", "") or "") or None,
                    "description": str(getattr(row, "description", "") or "") or None,
                },
            )
    writer.flush()


_COMMODITY_CATEGORY_MAP = {
    "농산물": ("agriculture", "USD/unit"),
    "비철금속": ("base_metals", "USD/ton"),
    "귀금속": ("precious_metals", "USD/oz"),
    "에너지": ("energy", "USD"),
}


def _ingest_quantplatform_commodity(
    writer: BatchWriter,
    aliases: dict[str, dict[str, str]],
) -> None:
    if not QP_COMMODITY.exists():
        log.warning("skip commodity: %s missing", QP_COMMODITY)
        return
    for category_dir in QP_COMMODITY.iterdir():
        if not category_dir.is_dir():
            continue
        cat_name = category_dir.name
        cat_tag, default_unit = _COMMODITY_CATEGORY_MAP.get(
            cat_name, ("commodity", "USD")
        )
        for path in sorted(category_dir.glob("*.csv")):
            stem = path.stem
            series_id = _resolve_series_id(
                aliases,
                "commodity",
                stem,
                fallback_native_id=f"legacy:commodity:{stem}",
            )
            try:
                df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
            except Exception as exc:
                log.error("read fail %s: %s", path, exc)
                continue
            if "date" not in df.columns or "value" not in df.columns:
                log.warning("skip %s: columns %s", path.name, list(df.columns))
                continue
            for row in df.itertuples(index=False):
                writer.add(
                    source_id=LEGACY_SRC_COMMODITY,
                    series_id=series_id,
                    date=_norm_date(getattr(row, "date", None)) or "",
                    value=_norm_value(getattr(row, "value", None)),
                    unit=default_unit,
                    meta={
                        "legacy_source": "quantplatform_commodity",
                        "commodity_name": stem,
                        "category_ko": cat_name,
                        "category": cat_tag,
                        "legacy_file": str(path.relative_to(QP_MACRO)),
                    },
                )
    writer.flush()


def _normalize_macro_series_id(raw: str) -> str:
    """macro_series stores ECOS/KOSIS IDs with ``:`` separator; the aliases
    file uses ``/``. Rewrite so both sources land on the same series_id."""
    if not raw:
        return "legacy:unknown"
    # Only rewrite when the shape looks like stat_code:item_code (digits/Ys)
    # to avoid mangling ids like ``US_YIELD_SPREAD_10Y2Y``.
    if ":" in raw and "/" not in raw:
        head, _, tail = raw.partition(":")
        if head and tail:
            # stat_code portion is typically 6-7 chars ending with a letter
            # followed by 3-4 digits; safe enough to rewrite when both
            # halves look like codes (no spaces, <=32 chars each).
            if len(head) <= 16 and len(tail) <= 16 and " " not in raw:
                return f"{head}/{tail}"
    return raw


def _ingest_quantdb_history(writer: BatchWriter) -> None:
    """Stream macro_series rows out of the 751 MB history.db."""
    if not QDB_HISTORY_DB.exists():
        log.warning("skip QDB history: %s missing", QDB_HISTORY_DB)
        return
    con = sqlite3.connect(f"file:{QDB_HISTORY_DB.as_posix()}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM macro_series")
        total = cur.fetchone()[0]
        log.info("QDB macro_series rows to scan: %s", f"{total:,}")
        cur.execute(
            "SELECT series_id, trade_date, value, source, frequency, unit,"
            " as_of_timestamp FROM macro_series"
        )
        processed = 0
        while True:
            rows = cur.fetchmany(5_000)
            if not rows:
                break
            for series_id, trade_date, value, source, frequency, unit, as_of in rows:
                source_id = LEGACY_SOURCE_PREFIX_MAP.get(
                    (source or "").strip(),
                    LEGACY_SRC_MACRO_DB,
                )
                normalized_id = _normalize_macro_series_id(
                    str(series_id) if series_id else ""
                )
                writer.add(
                    source_id=source_id,
                    series_id=normalized_id,
                    date=_norm_date(trade_date) or "",
                    value=_norm_value(value),
                    unit=str(unit) if unit else None,
                    meta={
                        "legacy_source": "quantdb_quant_platform_history",
                        "original_source": source,
                        "original_series_id": series_id,
                        "frequency": frequency,
                        "as_of_timestamp": as_of,
                    },
                )
            processed += len(rows)
            if processed % 50_000 < 5_000:
                log.info(
                    "  macro_series scanned %s / %s",
                    f"{processed:,}",
                    f"{total:,}",
                )
    finally:
        con.close()
    writer.flush()


# --------------------------- driver -----------------------------------------


SOURCE_CHOICES = [
    "all",
    "quantplatform_ecos",
    "quantplatform_commodity",
    "quantdb_history",
]


def _run_source(
    name: str,
    con: sqlite3.Connection,
    aliases: dict[str, dict[str, str]],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    log.info("===== %s =====", name)
    writer = BatchWriter(con, dry_run=dry_run, tag=name)
    t0 = datetime.utcnow()
    if name == "quantplatform_ecos":
        _ingest_quantplatform_ecos(writer, aliases)
    elif name == "quantplatform_commodity":
        _ingest_quantplatform_commodity(writer, aliases)
    elif name == "quantdb_history":
        _ingest_quantdb_history(writer)
    else:
        raise ValueError(name)
    writer.flush()
    dt = (datetime.utcnow() - t0).total_seconds()
    summary = {
        "source": name,
        "rows_in": writer.total_in,
        "rows_written": writer.total_out,
        "by_source_id": dict(writer.by_source),
        "distinct_series": len(writer.by_series),
        "elapsed_sec": round(dt, 1),
    }
    log.info(
        "[%s] done: in=%s written=%s series=%s elapsed=%ss",
        name,
        f"{writer.total_in:,}",
        f"{writer.total_out:,}",
        len(writer.by_series),
        round(dt, 1),
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default="all",
        choices=SOURCE_CHOICES,
        help="Which legacy archive to import (default: all).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and count without writing to ky.db.",
    )
    args = parser.parse_args()

    log_path = _setup_logging()
    log.info("log file: %s", log_path)

    aliases = _load_aliases()
    log.info(
        "aliases loaded: %s namespaces (%s entries total)",
        len(aliases),
        sum(len(v) for v in aliases.values()),
    )

    init_db()
    reset_engine_cache()

    con = _open_dest()

    # Snapshot before counts
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM observations")
    rows_before = cur.fetchone()[0]
    log.info("observations rows BEFORE: %s", f"{rows_before:,}")

    tasks = (
        [s for s in SOURCE_CHOICES if s != "all"]
        if args.source == "all"
        else [args.source]
    )
    summaries: list[dict[str, Any]] = []
    for task in tasks:
        summaries.append(_run_source(task, con, aliases, dry_run=args.dry_run))

    cur.execute("SELECT COUNT(*) FROM observations")
    rows_after = cur.fetchone()[0]
    log.info(
        "observations rows AFTER: %s (delta %s%s)",
        f"{rows_after:,}",
        f"+{rows_after - rows_before:,}"
        if rows_after >= rows_before
        else f"{rows_after - rows_before:,}",
        " (dry-run)" if args.dry_run else "",
    )

    cur.execute(
        "SELECT source_id, COUNT(*) FROM observations GROUP BY source_id ORDER BY 2 DESC"
    )
    by_source = cur.fetchall()
    log.info("observations by source_id (post-import):")
    for src, n in by_source:
        log.info("  %s: %s", src, f"{n:,}")

    summary_path = LOG_DIR / f"import_legacy_macro_summary_{datetime.utcnow():%Y%m%d_%H%M%S}.json"
    summary_path.write_text(
        json.dumps(
            {
                "rows_before": rows_before,
                "rows_after": rows_after,
                "dry_run": args.dry_run,
                "sources": summaries,
                "observations_by_source": dict(by_source),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    log.info("summary json: %s", summary_path)

    con.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
