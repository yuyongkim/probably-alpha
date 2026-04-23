"""Audit and repair Hangul names in the ``universe`` table of ``ky.db``.

The *Compass legacy union* work turned up reports of mojibake in the
``universe.name`` column. Running this script against the current database
confirms the stored values are in fact valid UTF-8 (``\xec\x82\xbc\xec\x84\xb1\xec\xa0\x84\xec\x9e\x90`` = ``삼성전자``) —
what looked broken was just a Windows ``cp949`` console rendering the UTF-8
bytes. We keep the script anyway because:

1. Future imports from different sources (e.g. a CP949-only CSV dumped from
   KRX's legacy portal) can silently re-introduce the bug.
2. A lightweight audit that flags ``U+FFFD``, CP949 round-trip candidates,
   and empty names gives us early warning before it reaches the UI.
3. If a canonical ``krx_universe.csv`` (UTF-8) is provided, we can overwrite
   any broken names from it as a last-resort repair.

Usage::

    # Audit-only, prints a JSON summary and exits 0 when clean.
    python scripts/repair_universe_names.py

    # Attempt auto-repair via CP949 round-trip on any row that looks broken.
    python scripts/repair_universe_names.py --fix-roundtrip

    # Overwrite broken names from a UTF-8 CSV with columns (ticker,name[,market]).
    python scripts/repair_universe_names.py --csv path/to/krx_universe.csv --apply

Exit codes:
    0 — clean or repaired successfully
    2 — mojibake detected, no repair requested
    3 — DB unreadable / CSV unreadable
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

DB_PATH = Path.home() / ".ky-platform" / "data" / "ky.db"


def _looks_mojibake(name: str) -> Tuple[bool, str | None]:
    """Return ``(broken, suggested_fix)``.

    A name is considered broken if:

    - it contains the Unicode replacement character ``U+FFFD``;
    - it is completely empty / None (caller already filters NULL);
    - its bytes, re-interpreted as CP949 then UTF-8, yield a *different*
      plausible Hangul string (classic double-encode mojibake).
    """
    if not name:
        return True, None
    if "�" in name:
        return True, None
    # CP949 round-trip: if utf8-bytes were mistakenly read as cp949 and
    # re-encoded to utf8, decoding via cp949→utf8 restores the original.
    try:
        candidate = name.encode("cp949").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False, None
    if candidate == name:
        return False, None
    # Only treat as broken when the candidate is plausible Hangul (lots of
    # ``AC00-D7A3``) and the incumbent is mostly Latin + symbols.
    hangul = sum(1 for c in candidate if "가" <= c <= "힣")
    if hangul >= max(1, len(candidate) // 3):
        return True, candidate
    return False, None


def audit(conn: sqlite3.Connection) -> Dict[str, Any]:
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM universe").fetchone()[0]
    null_name = cur.execute(
        "SELECT COUNT(*) FROM universe WHERE name IS NULL OR name=''"
    ).fetchone()[0]

    broken: List[Dict[str, Any]] = []
    fixable: List[Dict[str, Any]] = []
    for tid, mkt, name in cur.execute(
        "SELECT ticker, market, name FROM universe WHERE name IS NOT NULL AND name<>''"
    ):
        is_bad, suggestion = _looks_mojibake(name)
        if not is_bad:
            continue
        entry = {"ticker": tid, "market": mkt, "name": name, "suggested": suggestion}
        broken.append(entry)
        if suggestion:
            fixable.append(entry)

    sample_names: Dict[str, str] = {}
    for tid in ("005930", "000660", "035420", "005380", "207940"):
        row = cur.execute(
            "SELECT name FROM universe WHERE ticker=? LIMIT 1", (tid,)
        ).fetchone()
        if row:
            sample_names[tid] = row[0]

    return {
        "db_path": str(DB_PATH),
        "universe_total": total,
        "null_or_empty_name": null_name,
        "broken_count": len(broken),
        "roundtrip_fixable": len(fixable),
        "broken_sample": broken[:10],
        "sample_majors": sample_names,
    }


def fix_roundtrip(conn: sqlite3.Connection, report: Dict[str, Any]) -> int:
    """Overwrite broken names using the CP949 round-trip candidate.

    Only touches rows flagged as ``roundtrip_fixable`` by :func:`audit`.
    Returns number of rows updated.
    """
    cur = conn.cursor()
    updated = 0
    for entry in report["broken_sample"]:  # replay path; full set comes from audit caller
        if not entry.get("suggested"):
            continue
        cur.execute(
            "UPDATE universe SET name=? WHERE ticker=? AND market=?",
            (entry["suggested"], entry["ticker"], entry["market"]),
        )
        updated += cur.rowcount
    conn.commit()
    return updated


def apply_csv(conn: sqlite3.Connection, csv_path: Path) -> Dict[str, int]:
    """Overwrite names from a canonical UTF-8 CSV.

    The CSV must have a header row with at minimum ``ticker`` and ``name``.
    ``market`` is optional and used to disambiguate cross-listed tickers.
    Only rows where the current DB name is flagged broken get overwritten;
    good rows are left untouched so we never regress a correct value.
    """
    cur = conn.cursor()
    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or "ticker" not in reader.fieldnames or "name" not in reader.fieldnames:
            raise SystemExit(f"CSV must have ticker,name columns — got {reader.fieldnames}")
        overwritten = 0
        skipped_clean = 0
        missing = 0
        for row in reader:
            ticker = (row.get("ticker") or "").strip()
            new_name = (row.get("name") or "").strip()
            if not ticker or not new_name:
                continue
            market = (row.get("market") or "").strip() or None
            if market:
                existing = cur.execute(
                    "SELECT name FROM universe WHERE ticker=? AND market=?",
                    (ticker, market),
                ).fetchone()
            else:
                existing = cur.execute(
                    "SELECT name FROM universe WHERE ticker=?", (ticker,)
                ).fetchone()
            if existing is None:
                missing += 1
                continue
            is_bad, _ = _looks_mojibake(existing[0] or "")
            if not is_bad and existing[0] == new_name:
                skipped_clean += 1
                continue
            if is_bad or not existing[0]:
                if market:
                    cur.execute(
                        "UPDATE universe SET name=? WHERE ticker=? AND market=?",
                        (new_name, ticker, market),
                    )
                else:
                    cur.execute(
                        "UPDATE universe SET name=? WHERE ticker=?",
                        (new_name, ticker),
                    )
                overwritten += cur.rowcount
            else:
                skipped_clean += 1
    conn.commit()
    return {
        "overwritten": overwritten,
        "already_clean": skipped_clean,
        "missing_in_db": missing,
    }


def main(argv: List[str] | None = None) -> int:
    # Windows consoles default to cp949; force utf-8 so Hangul renders
    # instead of the familiar ``�Ｚ����`` salad.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help=f"Path to ky.db (default: {DB_PATH})",
    )
    parser.add_argument(
        "--fix-roundtrip",
        action="store_true",
        help="Attempt CP949 round-trip repair on clearly mojibake rows",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="UTF-8 CSV with ticker,name[,market] to use as authoritative source",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write repair changes (otherwise dry-run audit only)",
    )
    args = parser.parse_args(argv)

    if not args.db.exists():
        print(f"ERROR: db not found at {args.db}", file=sys.stderr)
        return 3

    conn = sqlite3.connect(args.db)
    try:
        report = audit(conn)
        print(json.dumps(report, ensure_ascii=False, indent=2))

        if args.fix_roundtrip and args.apply:
            # Pull the full fixable set (not just the 10-row sample).
            cur = conn.cursor()
            fixed = 0
            for tid, mkt, name in cur.execute(
                "SELECT ticker, market, name FROM universe WHERE name IS NOT NULL AND name<>''"
            ):
                bad, candidate = _looks_mojibake(name)
                if bad and candidate:
                    cur.execute(
                        "UPDATE universe SET name=? WHERE ticker=? AND market=?",
                        (candidate, tid, mkt),
                    )
                    fixed += cur.rowcount
            conn.commit()
            print(json.dumps({"roundtrip_applied": fixed}, indent=2))

        if args.csv:
            if not args.csv.exists():
                print(f"ERROR: csv not found at {args.csv}", file=sys.stderr)
                return 3
            if not args.apply:
                print("--csv provided without --apply: dry-run, no rows changed")
            else:
                result = apply_csv(conn, args.csv)
                print(json.dumps({"csv_apply": result}, ensure_ascii=False, indent=2))

        if report["broken_count"] and not (args.fix_roundtrip or args.csv):
            return 2
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
