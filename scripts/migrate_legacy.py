#!/usr/bin/env python
"""Legacy data migration → ky.db.

Pulls OHLCV, Universe, and Financials (PIT) from the six-project
archive and lands them in ~/.ky-platform/data/ky.db. Source files are
strictly read-only; no network calls; re-runnable (idempotent upsert).

Examples::

    python scripts/migrate_legacy.py --source ohlcv
    python scripts/migrate_legacy.py --source universe
    python scripts/migrate_legacy.py --source financials
    python scripts/migrate_legacy.py --source all
    python scripts/migrate_legacy.py --source ohlcv --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "packages" / "core", ROOT / "packages" / "adapters"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from ky_core.storage import init_db  # noqa: E402
from ky_core.storage.db import _resolve_db_path, reset_engine_cache  # noqa: E402

LOG_DIR = ROOT / "runtime_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------- config / paths -----------------------------------

SRC_OHLCV_CC = Path("C:/Users/USER/Desktop/Company_Credit/data/ohlcv.db")
SRC_OHLCV_QP = Path("C:/Users/USER/Desktop/QuantPlatform/analysis/data/stock_data.db")

SRC_UNIV_KRX = Path("C:/Users/USER/Desktop/Company_Credit/config/krx_universe.csv")
SRC_UNIV_ETF = Path("C:/Users/USER/Desktop/Company_Credit/config/krx_etf_universe.csv")
SRC_UNIV_KIS_KOSPI = Path(
    "C:/Users/USER/Desktop/한국투자증권/_tmp_kis_repo/backtester/.master/kospi.csv"
)
SRC_UNIV_KIS_KOSDAQ = Path(
    "C:/Users/USER/Desktop/한국투자증권/_tmp_kis_repo/backtester/.master/kosdaq.csv"
)

SRC_FIN_CSV = Path("C:/Users/USER/Desktop/QuantPlatform/fundamentals/data/quarterly_financials_pit.csv")
SRC_FIN_DB = Path("C:/Users/USER/Desktop/Company_Credit/data/financial.db")

BATCH_SIZE = 20_000      # rows per upsert batch
LOG_EVERY_BATCHES = 5    # progress log cadence


# ------------------------- logging ------------------------------------------

def _setup_logging() -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"migrate_{ts}.log"
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


log = logging.getLogger("migrate")


# ------------------------- dest helpers -------------------------------------

def _open_dest(db_path: Path) -> sqlite3.Connection:
    """Open destination SQLite with WAL and bulk-friendly PRAGMAs."""
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA temp_store=MEMORY")
    con.execute("PRAGMA cache_size=-200000")  # ~200 MB
    con.execute("PRAGMA foreign_keys=OFF")
    return con


def _ensure_universe_columns(con: sqlite3.Connection) -> None:
    """ALTER the existing universe table to add industry + is_etf if missing."""
    cur = con.cursor()
    cols = {row[1] for row in cur.execute("PRAGMA table_info(universe)").fetchall()}
    if "industry" not in cols:
        log.info("ALTER universe ADD industry")
        cur.execute("ALTER TABLE universe ADD COLUMN industry VARCHAR(64)")
    if "is_etf" not in cols:
        log.info("ALTER universe ADD is_etf")
        cur.execute("ALTER TABLE universe ADD COLUMN is_etf BOOLEAN NOT NULL DEFAULT 0")
    con.commit()


# ------------------------- market inference ---------------------------------

_MARKET_CACHE: dict[str, str] = {}


def _infer_market_from_universe() -> dict[str, str]:
    """Build symbol -> market lookup from krx_universe CSV once."""
    if _MARKET_CACHE:
        return _MARKET_CACHE
    import csv
    if not SRC_UNIV_KRX.exists():
        return _MARKET_CACHE
    with SRC_UNIV_KRX.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = (row.get("symbol") or "").strip()
            if not sym:
                continue
            code = sym.split(".")[0]
            suffix = sym.split(".")[-1] if "." in sym else ""
            if suffix == "KS":
                _MARKET_CACHE[code] = "KOSPI"
            elif suffix == "KQ":
                _MARKET_CACHE[code] = "KOSDAQ"
    return _MARKET_CACHE


def _market_for(code: str) -> str:
    lookup = _infer_market_from_universe()
    return lookup.get(code, "UNKNOWN")


# ------------------------- OHLCV migration ----------------------------------

def _batched_executemany(
    con: sqlite3.Connection,
    sql: str,
    rows: Iterable[tuple],
    batch_size: int = BATCH_SIZE,
    label: str = "rows",
) -> int:
    total = 0
    buf: list[tuple] = []
    batch_n = 0
    t0 = time.perf_counter()
    last_log = t0
    for row in rows:
        buf.append(row)
        if len(buf) >= batch_size:
            con.executemany(sql, buf)
            con.commit()
            total += len(buf)
            batch_n += 1
            buf.clear()
            now = time.perf_counter()
            if now - last_log >= 30.0 or batch_n % LOG_EVERY_BATCHES == 0:
                rate = total / max(now - t0, 1e-6)
                log.info("  %s: %s written (%.0f/s)", label, f"{total:,}", rate)
                last_log = now
    if buf:
        con.executemany(sql, buf)
        con.commit()
        total += len(buf)
    log.info("  %s: %s written total", label, f"{total:,}")
    return total


def _iter_ohlcv_cc(src: sqlite3.Connection) -> Iterable[tuple]:
    """Iterate Company_Credit ohlcv rows as destination tuples."""
    cur = src.cursor()
    cur.execute(
        "SELECT symbol, trade_date, open, high, low, close, volume "
        "FROM ohlcv ORDER BY symbol, trade_date"
    )
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    src_id = "company_credit"
    owner = "self"
    while True:
        chunk = cur.fetchmany(50_000)
        if not chunk:
            break
        for sym, ymd, op, hi, lo, cl, vol in chunk:
            if cl is None or cl <= 0:
                continue
            if not ymd or len(ymd) != 8:
                continue
            iso = f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}"
            mkt = _market_for(sym)
            yield (
                sym,           # symbol
                mkt,           # market
                iso,           # date
                op, hi, lo, cl,
                int(vol) if vol is not None else None,
                None,          # adj_close
                src_id,        # source_id
                now,           # fetched_at
                owner,         # owner_id
            )


def _iter_ohlcv_qp(src: sqlite3.Connection) -> Iterable[tuple]:
    """Iterate QuantPlatform stock_prices rows as destination tuples."""
    cur = src.cursor()
    cur.execute(
        "SELECT stock_code, trade_date, open_price, high_price, low_price, "
        "close_price, volume FROM stock_prices ORDER BY stock_code, trade_date"
    )
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    src_id = "quant_platform"
    owner = "self"
    while True:
        chunk = cur.fetchmany(50_000)
        if not chunk:
            break
        for sym, td, op, hi, lo, cl, vol in chunk:
            if cl is None or cl <= 0:
                continue
            if not td:
                continue
            # td is "YYYY-MM-DD HH:MM:SS" or "YYYY-MM-DD"
            iso = td[:10]
            if len(iso) != 10 or iso[4] != "-":
                continue
            mkt = _market_for(sym)
            yield (
                sym,
                mkt,
                iso,
                op, hi, lo, cl,
                int(vol) if vol is not None else None,
                None,
                src_id,
                now,
                owner,
            )


_OHLCV_UPSERT_SQL = """
INSERT INTO ohlcv (
    symbol, market, date, open, high, low, close, volume, adj_close,
    source_id, fetched_at, owner_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(owner_id, symbol, date) DO UPDATE SET
    market = CASE WHEN excluded.market != 'UNKNOWN' THEN excluded.market ELSE ohlcv.market END,
    open = COALESCE(excluded.open, ohlcv.open),
    high = COALESCE(excluded.high, ohlcv.high),
    low = COALESCE(excluded.low, ohlcv.low),
    close = excluded.close,
    volume = COALESCE(excluded.volume, ohlcv.volume),
    adj_close = COALESCE(excluded.adj_close, ohlcv.adj_close),
    source_id = excluded.source_id,
    fetched_at = excluded.fetched_at
"""


def migrate_ohlcv(dry_run: bool = False) -> dict[str, int]:
    stats = {"cc": 0, "qp": 0}
    log.info("=== OHLCV migration ===")
    if not SRC_OHLCV_CC.exists():
        log.warning("Company_Credit ohlcv.db missing: %s", SRC_OHLCV_CC)
    if not SRC_OHLCV_QP.exists():
        log.warning("QuantPlatform stock_data.db missing: %s", SRC_OHLCV_QP)

    dest_path = _resolve_db_path()
    log.info("dest: %s", dest_path)

    if dry_run:
        for key, label, src, tbl in (
            ("cc", "company_credit", SRC_OHLCV_CC, "ohlcv"),
            ("qp", "quant_platform", SRC_OHLCV_QP, "stock_prices"),
        ):
            if not src.exists():
                continue
            con = sqlite3.connect(str(src))
            n = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            log.info("  [dry-run] %s: %s rows", label, f"{n:,}")
            stats[key] = n
            con.close()
        return stats

    # Ensure schema present
    init_db()
    reset_engine_cache()

    con = _open_dest(dest_path)

    if SRC_OHLCV_CC.exists():
        log.info("Iterating Company_Credit ohlcv.db ...")
        src = sqlite3.connect(str(SRC_OHLCV_CC))
        src.execute("PRAGMA query_only=ON")
        try:
            n = _batched_executemany(
                con, _OHLCV_UPSERT_SQL, _iter_ohlcv_cc(src),
                label="ohlcv[cc]",
            )
            stats["cc"] = n
        finally:
            src.close()

    if SRC_OHLCV_QP.exists():
        log.info("Iterating QuantPlatform stock_data.db ...")
        src = sqlite3.connect(str(SRC_OHLCV_QP))
        src.execute("PRAGMA query_only=ON")
        try:
            n = _batched_executemany(
                con, _OHLCV_UPSERT_SQL, _iter_ohlcv_qp(src),
                label="ohlcv[qp]",
            )
            stats["qp"] = n
        finally:
            src.close()

    con.close()
    return stats


# ------------------------- Universe migration -------------------------------

def _read_csv(path: Path, encoding: str = "utf-8-sig") -> list[dict[str, str]]:
    """Read CSV with BOM-tolerant UTF-8 by default. KIS master files have BOM."""
    import csv
    if not path.exists():
        log.warning("Universe CSV missing: %s", path)
        return []
    with path.open(encoding=encoding) as f:
        return list(csv.DictReader(f))


_UNIV_UPSERT_SQL = """
INSERT INTO universe (
    ticker, market, name, sector, industry, is_etf, meta, updated_at, owner_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(ticker, market, owner_id) DO UPDATE SET
    name     = COALESCE(excluded.name,     universe.name),
    sector   = COALESCE(excluded.sector,   universe.sector),
    industry = COALESCE(excluded.industry, universe.industry),
    -- is_etf: sticky-true. Once flagged as ETF, don't demote.
    is_etf   = CASE WHEN excluded.is_etf = 1 THEN 1 ELSE universe.is_etf END,
    meta     = COALESCE(excluded.meta,     universe.meta),
    updated_at = excluded.updated_at
"""


def migrate_universe(dry_run: bool = False) -> dict[str, int]:
    stats: dict[str, int] = {}
    log.info("=== Universe migration ===")

    dest_path = _resolve_db_path()
    init_db()
    reset_engine_cache()

    con = _open_dest(dest_path)
    _ensure_universe_columns(con)

    now_iso = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    owner = "self"
    total_rows: list[tuple] = []

    # 1) krx_universe.csv (primary — has sector/industry)
    rows = _read_csv(SRC_UNIV_KRX)
    stats["krx"] = len(rows)
    for r in rows:
        sym = (r.get("symbol") or "").strip()
        if not sym:
            continue
        code = sym.split(".")[0]
        suffix = sym.split(".")[-1] if "." in sym else ""
        if suffix == "KS":
            mkt = "KOSPI"
        elif suffix == "KQ":
            mkt = "KOSDAQ"
        else:
            mkt = "KR"
        total_rows.append((
            code, mkt,
            (r.get("name") or None),
            (r.get("sector") or None),
            (r.get("industry") or None),
            0,                    # is_etf
            json.dumps({"src": "krx_universe", "orig_symbol": sym}, ensure_ascii=False),
            now_iso,
            owner,
        ))

    # 2) krx_etf_universe.csv
    rows = _read_csv(SRC_UNIV_ETF)
    stats["etf"] = len(rows)
    for r in rows:
        sym = (r.get("symbol") or "").strip()
        if not sym:
            continue
        code = sym.split(".")[0].zfill(6)
        mkt = "KOSPI"  # ETFs list on KOSPI
        meta = {
            "src": "krx_etf_universe",
            "asset_class": r.get("asset_class"),
            "theme": r.get("theme"),
            "leverage": r.get("leverage"),
            "inverse": r.get("inverse"),
            "benchmark_symbol": r.get("benchmark_symbol"),
        }
        total_rows.append((
            code, mkt,
            r.get("name") or None,
            None, None,
            1,
            json.dumps(meta, ensure_ascii=False),
            now_iso,
            owner,
        ))

    # 3) KIS master csvs (supplement — mostly names; already have via krx)
    for path, mkt in ((SRC_UNIV_KIS_KOSPI, "KOSPI"), (SRC_UNIV_KIS_KOSDAQ, "KOSDAQ")):
        rows = _read_csv(path)
        stats[f"kis_{mkt.lower()}"] = len(rows)
        for r in rows:
            code = str(r.get("code") or "").strip()
            if not code:
                continue
            code = code.zfill(6)
            total_rows.append((
                code, mkt,
                r.get("name") or None,
                None, None,
                0,
                json.dumps({"src": "kis_master"}, ensure_ascii=False),
                now_iso,
                owner,
            ))

    log.info("prepared %s universe rows (%s)", f"{len(total_rows):,}", stats)

    if dry_run:
        con.close()
        return stats

    n = _batched_executemany(con, _UNIV_UPSERT_SQL, iter(total_rows), label="universe")
    stats["written"] = n
    con.close()
    return stats


# ------------------------- Financials migration -----------------------------

_FIN_UPSERT_SQL = """
INSERT INTO financials_pit (
    corp_code, symbol, report_date, period_end, period_type,
    revenue, operating_income, net_income,
    total_assets, total_liabilities, total_equity,
    raw, source_id, fetched_at, owner_id
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(owner_id, symbol, period_end, period_type, source_id) DO UPDATE SET
    corp_code         = COALESCE(excluded.corp_code,         financials_pit.corp_code),
    report_date       = COALESCE(excluded.report_date,       financials_pit.report_date),
    revenue           = COALESCE(excluded.revenue,           financials_pit.revenue),
    operating_income  = COALESCE(excluded.operating_income,  financials_pit.operating_income),
    net_income        = COALESCE(excluded.net_income,        financials_pit.net_income),
    total_assets      = COALESCE(excluded.total_assets,      financials_pit.total_assets),
    total_liabilities = COALESCE(excluded.total_liabilities, financials_pit.total_liabilities),
    total_equity      = COALESCE(excluded.total_equity,      financials_pit.total_equity),
    raw               = COALESCE(excluded.raw,               financials_pit.raw),
    fetched_at        = excluded.fetched_at
"""


def _quarter_end(year: int, quarter: int) -> str:
    """Return ISO date for end of a reporting quarter."""
    if quarter == 1:
        return f"{year:04d}-03-31"
    if quarter == 2:
        return f"{year:04d}-06-30"
    if quarter == 3:
        return f"{year:04d}-09-30"
    return f"{year:04d}-12-31"


def _period_type_from_quarter(q: int) -> str:
    if q == 4:
        return "FY"
    return f"Q{q}"


def _iter_fin_csv() -> Iterable[tuple]:
    """Iterate quarterly_financials_pit.csv rows."""
    import pandas as pd
    if not SRC_FIN_CSV.exists():
        log.warning("PIT CSV missing: %s", SRC_FIN_CSV)
        return
    df = pd.read_csv(SRC_FIN_CSV, dtype={"stock_code": str})
    now_iso = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    src_id = "quant_platform_pit"
    owner = "self"
    log.info("PIT CSV rows: %s", f"{len(df):,}")

    for rec in df.itertuples(index=False):
        code = str(rec.stock_code).strip().zfill(6)
        year = int(rec.report_year)
        q = int(rec.report_quarter)
        period_end = str(rec.report_date) if rec.report_date else _quarter_end(year, q)
        period_end = period_end[:10]
        period_type = _period_type_from_quarter(q)
        report_date = str(rec.publish_date)[:10] if rec.publish_date else None

        def _f(x: Any) -> float | None:
            try:
                if x is None:
                    return None
                if isinstance(x, float) and x != x:  # NaN
                    return None
                return float(x)
            except (TypeError, ValueError):
                return None

        raw_extras = {
            "corp_name": getattr(rec, "corp_name", None),
            "report_type": getattr(rec, "report_type", None),
            "source_files": getattr(rec, "source_files", None),
        }
        raw_json = json.dumps({k: v for k, v in raw_extras.items() if v}, ensure_ascii=False)

        yield (
            None,                   # corp_code (PIT CSV doesn't carry DART corp_code)
            code,
            report_date,
            period_end,
            period_type,
            _f(rec.revenue),
            _f(rec.operating_income),
            _f(rec.net_income),
            _f(rec.total_assets),
            _f(rec.total_liabilities),
            _f(rec.total_equity),
            raw_json or None,
            src_id,
            now_iso,
            owner,
        )


# Korean account-name → PIT field mapping (Company_Credit `financials` table
# already aggregates these into a clean symbol/period/metric/value triple).
_CC_METRIC_MAP = {
    "매출액": "revenue",
    "영업이익": "operating_income",
    "당기순이익": "net_income",
}


def _parse_period(period: str, period_type: str) -> tuple[str, str] | None:
    """
    period: '2024' (annual) | '2024Q3' (quarterly)
    period_type: 'annual' | 'quarterly'
    Return (period_end_iso, pit_period_type).
    """
    try:
        if period_type == "annual" and len(period) == 4:
            year = int(period)
            return (f"{year:04d}-12-31", "FY")
        if period_type == "quarterly" and len(period) == 6 and period[4] == "Q":
            year = int(period[:4])
            q = int(period[5])
            if q not in (1, 2, 3, 4):
                return None
            return (_quarter_end(year, q), f"Q{q}" if q != 4 else "Q4")
    except ValueError:
        return None
    return None


def _iter_fin_cc_db() -> Iterable[tuple]:
    """Aggregate Company_Credit `financials` table rows into PIT rows.

    Groups by (symbol, period, period_type) and pivots the `metric`
    column into the columns defined by _CC_METRIC_MAP.
    """
    if not SRC_FIN_DB.exists():
        log.warning("financial.db missing: %s", SRC_FIN_DB)
        return
    con = sqlite3.connect(str(SRC_FIN_DB))
    con.execute("PRAGMA query_only=ON")
    cur = con.cursor()

    # Use the clean `financials` (symbol/period/period_type/metric/value) table
    # — far cheaper than pivoting financial_statements.
    metric_filter = ",".join(f"'{m}'" for m in _CC_METRIC_MAP)
    cur.execute(
        f"""SELECT symbol, period, period_type, metric, value
            FROM financials
            WHERE metric IN ({metric_filter})
            ORDER BY symbol, period, period_type"""
    )
    now_iso = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    src_id = "company_credit_fin"
    owner = "self"

    # Aggregate into a dict in-memory. ~60k distinct (symbol, period) groups
    # × 3 metrics = small working set.
    agg: dict[tuple[str, str, str], dict[str, Any]] = {}

    for sym, period, ptype, metric, value in cur.fetchall():
        parsed = _parse_period(period, ptype)
        if not parsed:
            continue
        period_end, pit_type = parsed
        key = (sym, period_end, pit_type)
        rec = agg.setdefault(key, {
            "corp_code": None,
            "symbol": sym,
            "report_date": None,
            "period_end": period_end,
            "period_type": pit_type,
            "revenue": None,
            "operating_income": None,
            "net_income": None,
            "total_assets": None,
            "total_liabilities": None,
            "total_equity": None,
        })
        col = _CC_METRIC_MAP.get(metric)
        if col and rec.get(col) is None:
            try:
                rec[col] = float(value) if value is not None else None
            except (TypeError, ValueError):
                pass

    con.close()
    log.info("company_credit_fin: aggregated %s PIT rows", f"{len(agg):,}")

    for rec in agg.values():
        yield (
            rec["corp_code"],
            rec["symbol"],
            rec["report_date"],
            rec["period_end"],
            rec["period_type"],
            rec["revenue"],
            rec["operating_income"],
            rec["net_income"],
            rec["total_assets"],
            rec["total_liabilities"],
            rec["total_equity"],
            None,
            src_id,
            now_iso,
            owner,
        )


def migrate_financials(dry_run: bool = False) -> dict[str, int]:
    stats: dict[str, int] = {}
    log.info("=== Financials migration ===")

    dest_path = _resolve_db_path()
    init_db()
    reset_engine_cache()

    con = _open_dest(dest_path)

    if dry_run:
        import pandas as pd
        if SRC_FIN_CSV.exists():
            n = len(pd.read_csv(SRC_FIN_CSV, usecols=["stock_code"]))
            stats["qp_pit"] = n
            log.info("  [dry-run] qp_pit: %s rows", f"{n:,}")
        if SRC_FIN_DB.exists():
            c2 = sqlite3.connect(str(SRC_FIN_DB))
            n = c2.execute(
                "SELECT COUNT(*) FROM financials WHERE metric IN ('매출액','영업이익','당기순이익')"
            ).fetchone()[0]
            stats["cc_fin"] = n
            log.info("  [dry-run] cc_fin metric rows: %s", f"{n:,}")
            c2.close()
        con.close()
        return stats

    if SRC_FIN_CSV.exists():
        log.info("Ingest quarterly_financials_pit.csv ...")
        n = _batched_executemany(
            con, _FIN_UPSERT_SQL, _iter_fin_csv(),
            label="fin[qp_pit]",
        )
        stats["qp_pit"] = n

    if SRC_FIN_DB.exists():
        log.info("Ingest Company_Credit financial.db ...")
        n = _batched_executemany(
            con, _FIN_UPSERT_SQL, _iter_fin_cc_db(),
            label="fin[cc_fin]",
        )
        stats["cc_fin"] = n

    con.close()
    return stats


# ------------------------- verification -------------------------------------

def verify(dest_path: Path) -> None:
    log.info("=== Verification ===")
    con = sqlite3.connect(str(dest_path))
    cur = con.cursor()

    n_ohlcv = cur.execute("SELECT COUNT(*) FROM ohlcv").fetchone()[0]
    n_symbols = cur.execute("SELECT COUNT(DISTINCT symbol) FROM ohlcv").fetchone()[0]
    log.info("ohlcv: %s rows, %s distinct symbols", f"{n_ohlcv:,}", f"{n_symbols:,}")

    latest = cur.execute(
        "SELECT date, close, market FROM ohlcv "
        "WHERE symbol='005930' ORDER BY date DESC LIMIT 1"
    ).fetchone()
    if latest:
        log.info("005930 latest: date=%s close=%s market=%s", *latest)
    else:
        log.warning("005930 not found in ohlcv")

    n_univ = cur.execute("SELECT COUNT(*) FROM universe").fetchone()[0]
    log.info("universe: %s rows", f"{n_univ:,}")
    samsung = cur.execute(
        "SELECT ticker, market, name, sector FROM universe WHERE ticker='005930' LIMIT 1"
    ).fetchone()
    if samsung:
        log.info("005930 universe: %s", samsung)

    n_fin = cur.execute("SELECT COUNT(*) FROM financials_pit").fetchone()[0]
    log.info("financials_pit: %s rows", f"{n_fin:,}")
    samsung_fin = cur.execute(
        "SELECT period_end, period_type, revenue, operating_income, net_income, source_id "
        "FROM financials_pit WHERE symbol='005930' ORDER BY period_end DESC LIMIT 5"
    ).fetchall()
    for row in samsung_fin:
        log.info("  005930 fin: %s", row)

    # Assertion pass/fail summary (non-fatal so we still commit + report)
    checks = [
        ("ohlcv rows > 5M",       n_ohlcv > 5_000_000),
        ("distinct symbols > 5k", n_symbols > 5_000),
        ("universe > 2.5k",       n_univ > 2_500),
        ("financials > 80k",      n_fin > 80_000),
        ("005930 latest close>0", bool(latest and latest[1] and latest[1] > 0),),
    ]
    for label, ok in checks:
        log.info("  check %-28s %s", label, "OK" if ok else "FAIL")
    con.close()


# ------------------------- CLI ----------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ky-platform legacy data migrator")
    p.add_argument("--source", type=str, required=True,
                   choices=["ohlcv", "universe", "financials", "all", "verify"],
                   help="which dataset to migrate")
    p.add_argument("--dry-run", action="store_true",
                   help="count-only, no writes")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    log_path = _setup_logging()
    log.info("=" * 72)
    log.info("migrate start: %s (dry_run=%s)", datetime.utcnow().isoformat(), args.dry_run)
    log.info("log file: %s", log_path)

    t0 = time.perf_counter()
    dest = _resolve_db_path()
    log.info("destination: %s", dest)

    summary: dict[str, Any] = {}

    if args.source in ("universe", "all"):
        t = time.perf_counter()
        summary["universe"] = migrate_universe(dry_run=args.dry_run)
        log.info("universe elapsed: %.1fs", time.perf_counter() - t)

    if args.source in ("ohlcv", "all"):
        t = time.perf_counter()
        summary["ohlcv"] = migrate_ohlcv(dry_run=args.dry_run)
        log.info("ohlcv elapsed: %.1fs", time.perf_counter() - t)

    if args.source in ("financials", "all"):
        t = time.perf_counter()
        summary["financials"] = migrate_financials(dry_run=args.dry_run)
        log.info("financials elapsed: %.1fs", time.perf_counter() - t)

    if args.source == "verify" or (args.source == "all" and not args.dry_run):
        verify(dest)

    elapsed = time.perf_counter() - t0
    log.info("=" * 72)
    log.info("migrate done in %.1fs", elapsed)
    log.info("summary: %s", json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
