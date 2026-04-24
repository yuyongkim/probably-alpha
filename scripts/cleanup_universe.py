#!/usr/bin/env python
"""Universe data cleanup — idempotent migration applied against ky.db.

Fixes three long-standing hygiene issues surfaced by /qa:

  1. is_etf flag only covers 12/4528 rows (prior audit). Set is_etf=1 for
     tickers that are ETFs by naming convention (KODEX, TIGER, ACE, PLUS,
     SOL, KBSTAR, KOSEF, KINDEX, ARIRANG, HANARO, TREX, RISE, HK) or by
     the "invalid KRX" ticker pattern XXXXX[A-Z]0 that fnguide
     legitimately rejects (these are ETP/index codes shipped by KRX).

  2. 12 duplicate (ticker, KOSDAQ) stub rows where KOSPI side holds the
     real company record and KOSDAQ side is name=NULL — delete the stub.
     (Symbol 100030 has real names on BOTH markets; preserved untouched.)

  3. Report-only: print counts so the operator can see what changed.

Idempotent: every statement is UPDATE/DELETE with a predicate that only
matches rows that still need the change. Re-running is a no-op after the
first successful run.

Usage:
    python scripts/cleanup_universe.py            # preview (dry-run)
    python scripts/cleanup_universe.py --apply    # write
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

# Force UTF-8 stdout — Windows cp949 console otherwise chokes on em-dash etc.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

DB_PATH = Path.home() / ".ky-platform" / "data" / "ky.db"

ETF_NAME_PREFIXES = (
    "KODEX", "TIGER", "ACE", "PLUS", "SOL", "KBSTAR", "KOSEF", "KINDEX",
    "ARIRANG", "HANARO", "TREX", "RISE", "HK ", "FOCUS", "WOORI", "MASTER",
    "SMART", "DAISHIN", "ASPECT", "100세", "ITF",
)

# Tickers shaped like `0000D0`, `0001S0`, `0007G0` … are KRX ETP/ETF product
# codes — 4 leading zeros, alnum+digit tail. They're not "invalid", they're a
# different product class than regular stocks.
ETF_TICKER_GLOB = "*[0-9][A-Z]0"


def survey(cur: sqlite3.Cursor) -> dict:
    out: dict = {}
    cur.execute("SELECT COUNT(*) FROM universe")
    out["total_universe"] = cur.fetchone()[0]
    cur.execute("SELECT is_etf, COUNT(*) FROM universe GROUP BY is_etf")
    out["is_etf_breakdown"] = dict(cur.fetchall())

    # Rows to flip to is_etf=1
    name_clauses = " OR ".join([f"UPPER(name) LIKE '{p}%'" for p in ETF_NAME_PREFIXES])
    sql = f"""
        SELECT COUNT(*) FROM universe
        WHERE (is_etf IS NULL OR is_etf = 0)
          AND name IS NOT NULL
          AND ({name_clauses})
    """
    cur.execute(sql)
    out["etf_flag_target_by_name"] = cur.fetchone()[0]

    cur.execute(f"""
        SELECT COUNT(*) FROM universe
        WHERE (is_etf IS NULL OR is_etf = 0)
          AND ticker GLOB '{ETF_TICKER_GLOB}'
    """)
    out["etf_flag_target_by_ticker"] = cur.fetchone()[0]

    # Duplicate stubs: same ticker exists twice, one side is KOSDAQ+name NULL,
    # other side is KOSPI+name NOT NULL.
    cur.execute("""
        SELECT kosdaq.ticker
        FROM universe kosdaq
        JOIN universe kospi
          ON kosdaq.ticker = kospi.ticker
         AND kosdaq.owner_id = kospi.owner_id
        WHERE kosdaq.market = 'KOSDAQ'
          AND kospi.market  = 'KOSPI'
          AND kosdaq.name IS NULL
          AND kospi.name  IS NOT NULL
    """)
    out["dup_stubs_to_delete"] = [r[0] for r in cur.fetchall()]

    return out


def apply(cur: sqlite3.Cursor) -> dict:
    out: dict = {}

    # 1. ETF flag by name prefix
    name_clauses = " OR ".join([f"UPPER(name) LIKE '{p}%'" for p in ETF_NAME_PREFIXES])
    cur.execute(f"""
        UPDATE universe
           SET is_etf = 1
         WHERE (is_etf IS NULL OR is_etf = 0)
           AND name IS NOT NULL
           AND ({name_clauses})
    """)
    out["etf_flagged_by_name"] = cur.rowcount

    # 2. ETF flag by ticker pattern (XXXXX[A-Z]0 KRX ETP codes)
    cur.execute(f"""
        UPDATE universe
           SET is_etf = 1
         WHERE (is_etf IS NULL OR is_etf = 0)
           AND ticker GLOB '{ETF_TICKER_GLOB}'
    """)
    out["etf_flagged_by_ticker"] = cur.rowcount

    # 3. Delete KOSDAQ stub rows that duplicate a real KOSPI entry
    cur.execute("""
        DELETE FROM universe
         WHERE rowid IN (
             SELECT kosdaq.rowid
               FROM universe kosdaq
               JOIN universe kospi
                 ON kosdaq.ticker = kospi.ticker
                AND kosdaq.owner_id = kospi.owner_id
              WHERE kosdaq.market = 'KOSDAQ'
                AND kospi.market  = 'KOSPI'
                AND kosdaq.name IS NULL
                AND kospi.name  IS NOT NULL
         )
    """)
    out["dup_stubs_deleted"] = cur.rowcount

    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="commit writes")
    p.add_argument("--db", default=str(DB_PATH))
    args = p.parse_args()

    db = Path(args.db)
    if not db.exists():
        print(f"db not found: {db}", file=sys.stderr)
        return 2

    conn = sqlite3.connect(str(db))
    cur = conn.cursor()

    print(f"db: {db}")
    print()
    print("=== survey (before) ===")
    s = survey(cur)
    for k, v in s.items():
        print(f"  {k}: {v}")

    if not args.apply:
        print()
        print("(dry-run — pass --apply to write)")
        return 0

    print()
    print("=== applying ===")
    result = apply(cur)
    for k, v in result.items():
        print(f"  {k}: {v}")
    conn.commit()
    print()
    print("=== survey (after) ===")
    s2 = survey(cur)
    for k, v in s2.items():
        print(f"  {k}: {v}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
