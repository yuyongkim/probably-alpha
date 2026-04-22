#!/usr/bin/env python
"""ky-platform data collection runner.

Examples:
    python scripts/collect.py --healthcheck
    python scripts/collect.py --source fred --series GDP,CPIAUCSL --start 2020-01-01
    python scripts/collect.py --source ecos --stat 722Y001 --item 0101000 --freq D \\
        --start 20240101 --end 20241231
    python scripts/collect.py --source eia --series PET.WCESTUS1.W
    python scripts/collect.py --source exim
    python scripts/collect.py --source dart --corp-code 00126380 --days 30
    python scripts/collect.py --source all-macro

Results are upserted into SQLite (``~/.ky-platform/data/ky.db``).
Logs are written to ``runtime_logs/collect_<timestamp>.log``.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

# ---- make sibling packages importable ---- #
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "packages" / "adapters", ROOT / "packages" / "core"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from ky_adapters.dart import DARTAdapter
from ky_adapters.ecos import ECOSAdapter
from ky_adapters.eia import EIAAdapter
from ky_adapters.exim import EXIMAdapter
from ky_adapters.fred import FREDAdapter
from ky_adapters.kis import KISAdapter
from ky_adapters.kosis import KOSISAdapter
from ky_core.storage import Repository
from ky_core.storage.presets import ECOS_SERIES, EIA_SERIES, FRED_SERIES

LOG_DIR = ROOT / "runtime_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _setup_logging() -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"collect_{ts}.log"
    # Force UTF-8 on Windows stdout so Korean text / em-dashes don't crash.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.handlers.clear()
    root.addHandler(fh)
    root.addHandler(sh)
    return log_path


log = logging.getLogger("collect")


# --------------------------------------------------------------------------- #
# Healthcheck                                                                 #
# --------------------------------------------------------------------------- #


def cmd_healthcheck() -> int:
    adapters = [
        FREDAdapter.from_settings(),
        ECOSAdapter.from_settings(),
        KOSISAdapter.from_settings(),
        EIAAdapter.from_settings(),
        EXIMAdapter.from_settings(),
        DARTAdapter.from_settings(),
        KISAdapter.from_settings(),
    ]
    failed = 0
    for a in adapters:
        try:
            h = a.healthcheck()
        except Exception as exc:  # noqa: BLE001
            h = {"ok": False, "source_id": a.source_id, "last_error": str(exc)}
        finally:
            a.close()
        status = "OK" if h.get("ok") else "FAIL"
        log.info("healthcheck %-6s %s %s", a.source_id, status, h)
        if not h.get("ok") and a.source_id != "kis":
            failed += 1
    return 0 if failed == 0 else 1


# --------------------------------------------------------------------------- #
# Per-source collectors                                                       #
# --------------------------------------------------------------------------- #


def _parse_date(raw: str | None, default: date) -> date:
    if not raw:
        return default
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise SystemExit(f"Invalid date: {raw!r}")


def collect_fred(series_ids: list[str], start: date, end: date, repo: Repository) -> int:
    fetched = 0
    with FREDAdapter.from_settings() as fred:
        for sid in series_ids:
            log.info("FRED fetching %s %s → %s", sid, start, end)
            obs = fred.get_series(sid, start=start, end=end)
            rows = [o.as_row() for o in obs]
            written = repo.upsert_observations(rows)
            log.info("FRED %s: %d rows upserted", sid, written)
            fetched += written
    return fetched


def collect_ecos(
    pairs: list[tuple[str, str, str]],
    start: str,
    end: str,
    repo: Repository,
) -> int:
    """pairs: list of (stat_code, item_code, freq)."""
    fetched = 0
    with ECOSAdapter.from_settings() as ecos:
        for stat, item, freq in pairs:
            log.info("ECOS fetching %s/%s %s %s→%s", stat, item, freq, start, end)
            obs = ecos.get_series(stat, item, start=start, end=end, freq=freq)
            rows = [o.as_row() for o in obs]
            written = repo.upsert_observations(rows)
            log.info("ECOS %s/%s: %d rows", stat, item, written)
            fetched += written
    return fetched


def collect_eia(series_ids: list[str], start: str | None, end: str | None, repo: Repository) -> int:
    fetched = 0
    with EIAAdapter.from_settings() as eia:
        for sid in series_ids:
            log.info("EIA fetching %s", sid)
            obs = eia.get_series(sid, start=start, end=end)
            rows = [o.as_row() for o in obs]
            written = repo.upsert_observations(rows)
            log.info("EIA %s: %d rows", sid, written)
            fetched += written
    return fetched


def collect_exim(repo: Repository, target: date | None = None) -> int:
    with EXIMAdapter.from_settings() as exim:
        rates = exim.get_rates(search_date=target)
        rows = [r.as_row() for r in rates]
        written = repo.upsert_observations(rows)
        log.info("EXIM: %d FX rows upserted", written)
        return written


def collect_dart(
    corp_code: str | None,
    days: int,
    page_count: int,
    repo: Repository,
) -> int:
    end = date.today()
    start = end - timedelta(days=days)
    with DARTAdapter.from_settings() as dart:
        filings = dart.list_disclosures(
            corp_code=corp_code, start=start, end=end, page_count=page_count
        )
        log.info("DART: fetched %d filings", len(filings))
        rows = [f.as_row() for f in filings]
        return repo.upsert_filings(rows)


# --------------------------------------------------------------------------- #
# Entrypoint                                                                  #
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ky-platform data collector")
    p.add_argument("--source", type=str, default=None,
                   help="fred | ecos | kosis | eia | exim | dart | all-macro")
    p.add_argument("--healthcheck", action="store_true")
    p.add_argument("--owner-id", type=str, default="self")

    # Common
    p.add_argument("--series", type=str, default=None, help="comma-separated series ids")
    p.add_argument("--start", type=str, default=None)
    p.add_argument("--end", type=str, default=None)

    # ECOS
    p.add_argument("--stat", type=str, default=None, help="ECOS stat_code")
    p.add_argument("--item", type=str, default=None, help="ECOS item_code")
    p.add_argument("--freq", type=str, default="D", help="ECOS freq (D/M/Q/Y)")

    # DART
    p.add_argument("--corp-code", type=str, default=None)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--page-count", type=int, default=20)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    log_path = _setup_logging()
    log.info("=" * 72)
    log.info("ky-platform collect start: %s", datetime.utcnow().isoformat())
    log.info("log file: %s", log_path)

    if args.healthcheck:
        return cmd_healthcheck()

    if not args.source:
        log.error("--source is required (or --healthcheck)")
        return 2

    repo = Repository(owner_id=args.owner_id)

    t0 = time.perf_counter()
    source = args.source.lower()
    total = 0

    if source == "fred":
        series_ids = args.series.split(",") if args.series else FRED_SERIES
        start = _parse_date(args.start, date.today() - timedelta(days=3650))
        end = _parse_date(args.end, date.today())
        total = collect_fred([s.strip() for s in series_ids if s.strip()], start, end, repo)

    elif source == "ecos":
        if args.stat and args.item:
            pairs = [(args.stat, args.item, args.freq)]
        else:
            pairs = [(s, i, f) for (s, i, f, _) in ECOS_SERIES]
        start = args.start or (date.today() - timedelta(days=365)).strftime("%Y%m%d")
        end = args.end or date.today().strftime("%Y%m%d")
        total = collect_ecos(pairs, start, end, repo)

    elif source == "eia":
        series_ids = args.series.split(",") if args.series else EIA_SERIES
        total = collect_eia(
            [s.strip() for s in series_ids if s.strip()],
            args.start,
            args.end,
            repo,
        )

    elif source == "exim":
        target = _parse_date(args.start, date.today()) if args.start else None
        total = collect_exim(repo, target=target)

    elif source == "dart":
        total = collect_dart(args.corp_code, args.days, args.page_count, repo)

    elif source == "kosis":
        log.warning("KOSIS requires --org-id and --tbl-id (not wired into CLI yet)")
        return 2

    elif source == "all-macro":
        fred_start = _parse_date(args.start, date.today() - timedelta(days=3650))
        fred_end = _parse_date(args.end, date.today())
        ecos_start = args.start or (date.today() - timedelta(days=365)).strftime("%Y%m%d")
        ecos_end = args.end or date.today().strftime("%Y%m%d")
        total += collect_fred(FRED_SERIES, fred_start, fred_end, repo)
        total += collect_ecos([(s, i, f) for (s, i, f, _) in ECOS_SERIES], ecos_start, ecos_end, repo)
        total += collect_eia(EIA_SERIES, None, None, repo)
        total += collect_exim(repo)

    else:
        log.error("unknown --source %s", source)
        return 2

    elapsed = time.perf_counter() - t0
    log.info("collect done: total_rows_upserted=%d elapsed=%.2fs", total, elapsed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
