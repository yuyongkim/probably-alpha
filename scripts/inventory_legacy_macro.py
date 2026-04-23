#!/usr/bin/env python
"""Inventory the legacy macro archives before bulk-importing into ky.db.

Outputs:
  runtime_logs/inventory_legacy_macro_YYYYMMDD.json

The companion importer (``scripts/import_legacy_macro.py``) consumes the
exact same set of sources, so this script's job is to pre-flight: count
rows, enumerate unique indicators, surface date ranges, and flag pairs of
files whose contents collide so we can dedupe before touching ky.db.

Source archives (all read-only):
  * ``C:/Users/USER/Desktop/QuantPlatform/macro/data/ecos/``
      - top-level ``ECOS_*.csv`` and ``FRED_*.csv`` snapshots (multiple
        timestamped copies; known to be duplicates)
      - ``카테고리별_그룹화/*.csv`` (14 category bundles, 220k rows; this is
        the curated superset the importer actually loads)
      - ``지표별_개별파일/*.csv`` (71 per-indicator files; bit-identical
        content as the category bundles)
  * ``C:/Users/USER/Desktop/QuantPlatform/macro/data/commodities/`` — 11
    CSVs with ``date,value`` only (id derived from filename)
  * ``C:/Users/USER/Desktop/QuantPlatform/macro/data/market_data.db`` —
    current snapshot only (NOT time series); inventoried for completeness
    but skipped by the importer.
  * ``C:/Users/USER/Desktop/QuantDB/mvp_platform/data/quant_platform_history.db``
    → ``macro_series`` (535k rows across 1,108 series)
  * ``C:/Users/USER/Desktop/QuantDB/mvp_platform/data/external/macro_ecos/``
    — bit-identical duplicate of the QuantPlatform ECOS directory. We only
    scan it for a hash-diff confirmation and skip it during import.

Usage::

    python scripts/inventory_legacy_macro.py
    python scripts/inventory_legacy_macro.py --out runtime_logs/custom.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "runtime_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

QP_MACRO = Path("C:/Users/USER/Desktop/QuantPlatform/macro/data")
QDB_MACRO_ECOS = Path(
    "C:/Users/USER/Desktop/QuantDB/mvp_platform/data/external/macro_ecos"
)
QDB_HISTORY_DB = Path(
    "C:/Users/USER/Desktop/QuantDB/mvp_platform/data/quant_platform_history.db"
)
QP_MARKET_DB = QP_MACRO / "market_data.db"


def _md5(path: Path, cap_mb: int = 50) -> str:
    h = hashlib.md5()
    size = path.stat().st_size
    if size > cap_mb * 1024 * 1024:
        return f"toolarge:{size}"
    with path.open("rb") as fp:
        h.update(fp.read())
    return h.hexdigest()


def _scan_csv_dir(
    root: Path,
    *,
    has_indicator_col: bool,
) -> dict[str, Any]:
    """Walk one CSV directory. Returns row/indicator/date metrics."""
    files: list[dict[str, Any]] = []
    total_rows = 0
    indicators: set[str] = set()
    min_date = "9999-12-31"
    max_date = "0000-01-01"

    for dirpath, _dirs, filenames in os.walk(root):
        for f in sorted(filenames):
            if not f.lower().endswith(".csv"):
                continue
            path = Path(dirpath) / f
            try:
                df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
            except Exception as exc:  # pragma: no cover
                files.append(
                    {
                        "path": str(path),
                        "error": f"{type(exc).__name__}:{exc}",
                    }
                )
                continue
            rows = len(df)
            if rows == 0:
                files.append({"path": str(path), "rows": 0})
                continue
            total_rows += rows
            info: dict[str, Any] = {
                "path": str(path),
                "rows": rows,
                "columns": list(df.columns),
                "mtime": datetime.utcfromtimestamp(
                    path.stat().st_mtime
                ).isoformat(),
            }
            if "date" in df.columns:
                dmin = str(df["date"].min())
                dmax = str(df["date"].max())
                info["date_range"] = [dmin, dmax]
                if dmin < min_date:
                    min_date = dmin
                if dmax > max_date:
                    max_date = dmax
            if has_indicator_col and "indicator" in df.columns:
                if "source" in df.columns:
                    ids = (
                        df["indicator"].astype(str)
                        + "|"
                        + df["source"].astype(str)
                    ).unique()
                else:
                    ids = df["indicator"].astype(str).unique()
                info["indicators"] = len(ids)
                indicators.update(ids.tolist())
            files.append(info)

    return {
        "root": str(root),
        "file_count": len([x for x in files if "rows" in x]),
        "total_rows": total_rows,
        "distinct_indicators": len(indicators),
        "date_range": (
            [min_date, max_date]
            if min_date != "9999-12-31"
            else None
        ),
        "files": files,
    }


def _inventory_sqlite(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {"path": str(db_path), "error": "missing"}
    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables: list[dict[str, Any]] = []
    for (name,) in cur.fetchall():
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{name}"')
            count = cur.fetchone()[0]
        except sqlite3.Error as exc:
            count = f"ERR:{exc}"
        tables.append({"table": name, "rows": count})
    # Deep dive on macro_series when present
    macro_detail: dict[str, Any] | None = None
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='macro_series'"
    )
    if cur.fetchone():
        cur.execute(
            "SELECT MIN(trade_date), MAX(trade_date),"
            " COUNT(DISTINCT series_id), COUNT(DISTINCT source) FROM macro_series"
        )
        dmin, dmax, distinct_series, distinct_sources = cur.fetchone()
        cur.execute("SELECT source, COUNT(*) FROM macro_series GROUP BY source")
        by_source = {row[0]: row[1] for row in cur.fetchall()}
        macro_detail = {
            "date_range": [dmin, dmax],
            "distinct_series": distinct_series,
            "distinct_sources": distinct_sources,
            "rows_by_source": by_source,
        }
    conn.close()
    return {
        "path": str(db_path),
        "size_bytes": db_path.stat().st_size,
        "tables": tables,
        "macro_series": macro_detail,
    }


def _collision_check() -> dict[str, Any]:
    """Confirm QDB external/macro_ecos == QP ecos directory (bit identical)."""
    if not QP_MACRO.exists() or not QDB_MACRO_ECOS.exists():
        return {"skipped": "one side missing"}
    diffs: list[str] = []
    same = 0
    for f in os.listdir(QP_MACRO / "ecos"):
        a = QP_MACRO / "ecos" / f
        b = QDB_MACRO_ECOS / f
        if not (a.is_file() and b.exists() and b.is_file()):
            continue
        if _md5(a) == _md5(b):
            same += 1
        else:
            diffs.append(f)
    return {
        "identical_top_level": same,
        "differing_top_level": diffs,
        "conclusion": (
            "QDB macro_ecos is a bit-identical duplicate; importer skips it."
            if not diffs
            else "Files differ — need manual review."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=None,
        help="Destination JSON (default: runtime_logs/inventory_legacy_macro_YYYYMMDD.json)",
    )
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    report: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat(),
        "ecos_top_level_csvs": _scan_csv_dir(
            QP_MACRO / "ecos",
            has_indicator_col=True,
        ),
        "ecos_categorized": _scan_csv_dir(
            QP_MACRO / "ecos" / "카테고리별_그룹화",
            has_indicator_col=True,
        ),
        "ecos_per_indicator": _scan_csv_dir(
            QP_MACRO / "ecos" / "지표별_개별파일",
            has_indicator_col=True,
        ),
        "commodities": _scan_csv_dir(
            QP_MACRO / "commodities",
            has_indicator_col=False,
        ),
        "quant_platform_history_db": _inventory_sqlite(QDB_HISTORY_DB),
        "quant_platform_market_db": _inventory_sqlite(QP_MARKET_DB),
        "collision_check_qp_vs_qdb_ecos": _collision_check(),
    }

    # Total row estimate considering which sources the importer loads
    load_rows = (
        (report["ecos_categorized"]["total_rows"])
        + (report["commodities"]["total_rows"])
    )
    macro_detail = report["quant_platform_history_db"].get("macro_series")
    if macro_detail:
        load_rows += sum(macro_detail["rows_by_source"].values())
    report["importer_load_estimate_rows"] = load_rows

    out = (
        Path(args.out)
        if args.out
        else LOG_DIR / f"inventory_legacy_macro_{datetime.utcnow():%Y%m%d}.json"
    )
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"  ECOS categorized rows ...... {report['ecos_categorized']['total_rows']:,}")
    print(f"  ECOS per-indicator rows .... {report['ecos_per_indicator']['total_rows']:,}")
    print(f"  ECOS top-level rows ........ {report['ecos_top_level_csvs']['total_rows']:,}")
    print(f"  Commodity rows ............. {report['commodities']['total_rows']:,}")
    if macro_detail:
        total_db = sum(macro_detail["rows_by_source"].values())
        print(f"  QDB macro_series rows ...... {total_db:,}")
    print(f"  Importer load estimate ..... {load_rows:,}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
