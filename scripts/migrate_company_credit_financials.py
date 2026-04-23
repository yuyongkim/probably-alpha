"""Bulk-migrate Company_Credit ``financial.db`` into ky-platform ``ky.db``.

Source (READ-ONLY): ``C:/Users/USER/Desktop/Company_Credit/data/financial.db``
Destination: ``~/.ky-platform/data/ky.db``

Migrates:

* ``financial_snapshot`` (2,495 rows) → ``fnguide_snapshots`` — one JSON payload
  per symbol, so the FnguideAdapter DB-first fallback can serve broad history
  without hammering Naver.
* ``financial_statements`` (1,716,997 rows) → ``financial_statements_db`` —
  per-account per-period quarterly/annual line items keyed by (symbol, period,
  period_type, account_name, source_id).

The script is idempotent — running it twice upserts the same rows. Use
``--dry-run`` to count what would be touched without writes. ``--validate-only``
runs Phase 2's assertions against sample payloads in the SOURCE DB. ``--sample
N`` caps the number of symbols migrated (for smoke testing).

Usage::

    python scripts/migrate_company_credit_financials.py             # full run
    python scripts/migrate_company_credit_financials.py --dry-run   # counts only
    python scripts/migrate_company_credit_financials.py --sample 50 # first 50 syms

Progress is logged both to stdout and ``runtime_logs/migrate_fnguide_*.log``.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator

SOURCE_DB = Path(r"C:/Users/USER/Desktop/Company_Credit/data/financial.db")

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "runtime_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"migrate_fnguide_{datetime.now():%Y%m%d_%H%M%S}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("migrate")


# --------------------------------------------------------------------------- #
# Source readers                                                              #
# --------------------------------------------------------------------------- #

def open_source() -> sqlite3.Connection:
    if not SOURCE_DB.exists():
        log.error("source DB missing: %s", SOURCE_DB)
        sys.exit(3)
    con = sqlite3.connect(f"file:{SOURCE_DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def iter_snapshot_rows(con: sqlite3.Connection, symbols: list[str] | None = None) -> Iterator[dict]:
    q = "SELECT * FROM financial_snapshot"
    args: tuple = ()
    if symbols:
        placeholders = ",".join("?" * len(symbols))
        q += f" WHERE symbol IN ({placeholders})"
        args = tuple(symbols)
    for row in con.execute(q, args):
        yield dict(row)


def iter_statement_rows(
    con: sqlite3.Connection, symbols: list[str] | None = None,
) -> Iterator[dict]:
    q = "SELECT * FROM financial_statements"
    args: tuple = ()
    if symbols:
        placeholders = ",".join("?" * len(symbols))
        q += f" WHERE symbol IN ({placeholders})"
        args = tuple(symbols)
    for row in con.execute(q, args):
        yield dict(row)


def iter_metric_rows(
    con: sqlite3.Connection, symbols: list[str] | None = None,
) -> Iterator[dict]:
    """``financial_metrics`` carries (per, pbr, eps, roe, ...) per period. We
    fold them into the snapshot payload so DB-first serves the same shape the
    adapter would otherwise return.
    """
    q = "SELECT symbol, period, metric, value FROM financial_metrics"
    args: tuple = ()
    if symbols:
        placeholders = ",".join("?" * len(symbols))
        q += f" WHERE symbol IN ({placeholders})"
        args = tuple(symbols)
    for row in con.execute(q, args):
        yield dict(row)


# --------------------------------------------------------------------------- #
# Payload builder                                                             #
# --------------------------------------------------------------------------- #

def snapshot_to_payload(snap: dict, metrics_by_period: dict[str, dict[str, float]] | None = None) -> dict:
    """Translate a ``financial_snapshot`` row into the FnguideSnapshot-shaped
    JSON payload that the REST endpoint already ships.

    The schema mirrors the live-adapter ``to_dict()`` output so downstream
    consumers (apps/web value viewer) need no change.
    """
    fetched_iso = snap.get("updated_at") or datetime.utcnow().isoformat()
    try:
        fetched_unix = datetime.fromisoformat(fetched_iso).timestamp()
    except Exception:  # noqa: BLE001
        fetched_unix = time.time()

    fm_rows: list[dict[str, Any]] = []
    if metrics_by_period:
        for period in sorted(metrics_by_period.keys(), reverse=True):
            row: dict[str, Any] = {"period": period}
            row.update(metrics_by_period[period])
            fm_rows.append(row)

    return {
        "symbol": snap["symbol"],
        "fetched_at": fetched_unix,
        "source": "company_credit_naver_snapshot",
        "degraded": False,
        "target_price": snap.get("target_price"),
        "investment_opinion": None,
        "consensus_recomm_score": snap.get("recommend_score"),
        "consensus_per": snap.get("cns_per"),
        "consensus_eps": snap.get("cns_eps"),
        "per": snap.get("per"),
        "pbr": snap.get("pbr"),
        "eps": snap.get("eps"),
        "bps": snap.get("bps"),
        "roe": snap.get("roe"),
        "roa": None,
        "debt_ratio": None,
        "dividend_yield": snap.get("dividend_yield"),
        "market_cap": snap.get("market_cap_krw"),
        "market_cap_raw": None,
        "foreign_ratio": snap.get("foreign_ratio"),
        "high_52w": snap.get("high_52w"),
        "low_52w": snap.get("low_52w"),
        "industry_code": None,
        "major_shareholder_name": None,
        "major_shareholder_pct": None,
        "float_ratio": None,
        "shares_outstanding": snap.get("shares_outstanding"),
        "beta_52w": None,
        "financials_quarterly": [],
        "financials_annual": [],
        "financial_metrics": fm_rows,
        "sector_comparison": {},
        "investor_trend": [],
        "peers": [],
        "summary_notes": [
            f"migrated from Company_Credit/financial.db updated_at={snap.get('updated_at')}",
        ],
        "sources_used": ["company_credit_naver_snapshot"],
    }


def bucket_metrics(rows: Iterable[dict]) -> dict[str, dict[str, dict[str, float]]]:
    """Group metric rows into {symbol: {period: {metric: value}}} form."""
    out: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        sym = r["symbol"]
        period = r["period"]
        metric = r["metric"]
        out[sym][period][metric] = r["value"]
    return out


# --------------------------------------------------------------------------- #
# Migration                                                                   #
# --------------------------------------------------------------------------- #

def migrate_snapshots(
    *, dry_run: bool, symbols: list[str] | None, batch_size: int = 1000,
) -> int:
    log.info("Phase 3a: financial_snapshot → fnguide_snapshots")
    from ky_core.storage import Repository
    repo = Repository()
    con = open_source()
    try:
        log.info("loading financial_metrics index (may take a few seconds)...")
        metrics_idx = bucket_metrics(iter_metric_rows(con, symbols))
        log.info("  indexed %d symbols × %d (symbol,period) buckets",
                 len(metrics_idx),
                 sum(len(v) for v in metrics_idx.values()))

        count = 0
        for snap in iter_snapshot_rows(con, symbols):
            sym = snap["symbol"]
            period_metrics = metrics_idx.get(sym, {})
            payload = snapshot_to_payload(snap, period_metrics)
            # Parse the source updated_at so downstream freshness checks reflect
            # the actual data age — not this import's wall clock.
            captured_at = None
            ua = snap.get("updated_at")
            if ua:
                try:
                    captured_at = datetime.fromisoformat(ua)
                except ValueError:
                    captured_at = None
            if not dry_run:
                repo.upsert_fnguide_snapshot(
                    sym,
                    json.dumps(payload, ensure_ascii=False),
                    source="company_credit_naver_snapshot",
                    degraded=False,
                    fetched_at=captured_at,
                )
            count += 1
            if count % 200 == 0:
                log.info("  snapshots: %d", count)
        log.info("Phase 3a done. snapshots written=%d dry_run=%s", count, dry_run)
        return count
    finally:
        con.close()


def migrate_statements(
    *, dry_run: bool, symbols: list[str] | None, batch_size: int = 10000,
) -> int:
    log.info("Phase 3b: financial_statements → financial_statements_db")
    from ky_core.storage import Repository
    repo = Repository()
    con = open_source()
    try:
        total = con.execute(
            "SELECT COUNT(*) FROM financial_statements"
            + (f" WHERE symbol IN ({','.join('?' * len(symbols))})" if symbols else ""),
            tuple(symbols) if symbols else (),
        ).fetchone()[0]
        log.info("  source rows to process: %d", total)

        buf: list[dict] = []
        count = 0
        t0 = time.perf_counter()
        for row in iter_statement_rows(con, symbols):
            buf.append({
                "symbol": row["symbol"],
                "period": row["period"],
                "period_type": row["period_type"],
                "account_code": row.get("account_code"),
                "account_name": row["account_name"],
                "account_level": row.get("account_level"),
                "value": row.get("value"),
                "yoy": row.get("yoy"),
                "is_estimate": bool(row.get("is_estimate") or 0),
                "source_id": row.get("source") or "naver_comp",
            })
            if len(buf) >= batch_size:
                if not dry_run:
                    repo.upsert_financial_statements(buf)
                count += len(buf)
                buf.clear()
                elapsed = time.perf_counter() - t0
                rate = count / elapsed if elapsed else 0
                eta = (total - count) / rate if rate else 0
                log.info("  statements: %d / %d (%.0f rows/s, eta %.0fs)",
                         count, total, rate, eta)
        if buf:
            if not dry_run:
                repo.upsert_financial_statements(buf)
            count += len(buf)
        log.info("Phase 3b done. statements written=%d dry_run=%s", count, dry_run)
        return count
    finally:
        con.close()


def validate_only(symbols: list[str] | None) -> None:
    con = open_source()
    try:
        counts = {}
        for t in ("financial_snapshot", "financial_statements",
                  "financial_metrics", "financials"):
            counts[t] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        log.info("source table counts: %s", counts)
        syms = {r[0] for r in con.execute(
            "SELECT DISTINCT symbol FROM financial_snapshot").fetchall()}
        log.info("distinct symbols in snapshot: %d", len(syms))
        sample = next(iter(syms))
        payload = snapshot_to_payload(
            next(iter(iter_snapshot_rows(con, [sample]))),
            bucket_metrics(iter_metric_rows(con, [sample])).get(sample, {}),
        )
        log.info("sample payload (%s): %s", sample, json.dumps(payload,
                 ensure_ascii=False)[:200] + "...")
    finally:
        con.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="do not write")
    p.add_argument("--validate-only", action="store_true",
                   help="sanity-check source, skip writes")
    p.add_argument("--sample", type=int, default=0,
                   help="only migrate N first symbols (0 = all)")
    p.add_argument("--skip-snapshots", action="store_true")
    p.add_argument("--skip-statements", action="store_true")
    p.add_argument("--batch-size", type=int, default=10000)
    args = p.parse_args()

    log.info("=" * 60)
    log.info("migrate_company_credit_financials  (log=%s)", LOG_FILE.name)
    log.info("=" * 60)
    log.info("source: %s", SOURCE_DB)
    log.info("dest:   %s", Path.home() / ".ky-platform" / "data" / "ky.db")

    # Ensure tables exist in ky.db.
    from ky_core.storage import init_db
    init_db()

    if args.validate_only:
        validate_only(None)
        return

    symbols: list[str] | None = None
    if args.sample:
        con = open_source()
        try:
            symbols = [r[0] for r in con.execute(
                "SELECT DISTINCT symbol FROM financial_snapshot ORDER BY symbol LIMIT ?",
                (args.sample,),
            ).fetchall()]
            log.info("sample mode: %d symbols", len(symbols))
        finally:
            con.close()

    n_snap = n_stmt = 0
    if not args.skip_snapshots:
        n_snap = migrate_snapshots(dry_run=args.dry_run, symbols=symbols)
    if not args.skip_statements:
        n_stmt = migrate_statements(dry_run=args.dry_run, symbols=symbols,
                                    batch_size=args.batch_size)

    log.info("=" * 60)
    log.info("DONE  snapshots=%d  statements=%d  dry_run=%s",
             n_snap, n_stmt, args.dry_run)
    log.info("=" * 60)


if __name__ == "__main__":
    main()
