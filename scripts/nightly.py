#!/usr/bin/env python
"""Nightly data-collection runner for ky-platform.

Single entrypoint scheduled by Windows Task Scheduler / cron at ~02:00 KST.

Pipeline (each stage runs independently; partial success is OK):

  1. KIS daily OHLCV pull for every tradable universe symbol whose latest
     OHLCV row is more than ``KIS_STALE_BDAYS`` business days old.
  2. FnGuide / Naver snapshot refresh for every universe row whose snapshot
     is stale (> 24h since ``fetched_at``). Worker-pooled for throughput.
  3. DART disclosures for the last ``DART_WINDOW_DAYS`` days (typically 1;
     widened to 3 to re-catch filings that surfaced late).
  4. Macro refreshes: FRED / ECOS / KOSIS / EIA / EXIM for the last
     ``MACRO_WINDOW_DAYS`` days.

Each stage captures wall-clock duration, rows-added, and any exception.

Results are written to::

    ~/.ky-platform/data/ops/nightly_run_<UTC_YYYYMMDD_HHMMSS>.json

Usage::

    python scripts/nightly.py                 # full run
    python scripts/nightly.py --dry-run       # list stages, touch nothing
    python scripts/nightly.py --only kis      # single stage
    python scripts/nightly.py --only fred,dart

Exit codes::

    0  all stages succeeded (may include "0 rows added")
    1  one or more stages raised — the run report still lands on disk
    2  bad invocation (unknown --only value, etc.)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

# ---- make sibling packages importable -------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "packages" / "adapters", ROOT / "packages" / "core"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

OPS_DIR = Path.home() / ".ky-platform" / "data" / "ops"
OPS_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = ROOT / "runtime_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# Stage identifiers (stable — frontend keys off these).
STAGES = ("kis_daily", "fnguide_refresh", "dart_disclosures", "macro_refresh")

# Tunables — overridable via env vars for one-off experiments.
KIS_STALE_BDAYS = int(os.getenv("KY_NIGHTLY_KIS_STALE_BDAYS", "5"))
FNGUIDE_STALE_HOURS = int(os.getenv("KY_NIGHTLY_FNGUIDE_STALE_HOURS", "24"))
FNGUIDE_MAX_SYMBOLS = int(os.getenv("KY_NIGHTLY_FNGUIDE_MAX", "2500"))
DART_WINDOW_DAYS = int(os.getenv("KY_NIGHTLY_DART_DAYS", "3"))
MACRO_WINDOW_DAYS = int(os.getenv("KY_NIGHTLY_MACRO_DAYS", "7"))


# --------------------------------------------------------------------------- #
# Logging                                                                     #
# --------------------------------------------------------------------------- #


def _setup_logging() -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"nightly_{ts}.log"
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


log = logging.getLogger("nightly")


# --------------------------------------------------------------------------- #
# Report dataclasses                                                          #
# --------------------------------------------------------------------------- #


@dataclass
class StageResult:
    name: str
    status: str = "pending"          # "ok" | "fail" | "skipped" | "dry_run"
    started_at: str | None = None
    ended_at: str | None = None
    duration_s: float = 0.0
    rows_added: int = 0
    symbols_processed: int = 0
    error: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class NightlyReport:
    kind: str = "nightly"
    started_at: str = ""
    ended_at: str = ""
    duration_s: float = 0.0
    total_rows_added: int = 0
    stages: list[StageResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    partial_success: bool = False
    dry_run: bool = False
    only: list[str] | None = None
    log_path: str | None = None

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        return d


# --------------------------------------------------------------------------- #
# Stage runner                                                                #
# --------------------------------------------------------------------------- #


def _run_stage(
    name: str,
    fn: Callable[[], dict[str, Any]],
    *,
    dry_run: bool,
) -> StageResult:
    res = StageResult(name=name)
    if dry_run:
        res.status = "dry_run"
        res.detail = {"note": "dry-run — skipped execution"}
        log.info("[%s] dry-run: would execute", name)
        return res
    res.started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    try:
        out = fn() or {}
        res.rows_added = int(out.get("rows_added", 0))
        res.symbols_processed = int(out.get("symbols_processed", 0))
        res.detail = {k: v for k, v in out.items()
                      if k not in {"rows_added", "symbols_processed"}}
        res.status = "ok"
        log.info(
            "[%s] ok rows=%d symbols=%d", name, res.rows_added, res.symbols_processed
        )
    except Exception as exc:  # noqa: BLE001 — capture + continue
        res.status = "fail"
        res.error = f"{type(exc).__name__}: {exc}"
        log.exception("[%s] FAILED: %s", name, exc)
    finally:
        res.ended_at = datetime.now(timezone.utc).isoformat()
        res.duration_s = round(time.perf_counter() - t0, 3)
    return res


# --------------------------------------------------------------------------- #
# Stage 1 — KIS daily OHLCV                                                   #
# --------------------------------------------------------------------------- #


def stage_kis_daily() -> dict[str, Any]:
    """Refresh end-of-day OHLCV via KIS.

    The KIS adapter does not yet expose a true historical daily endpoint, so
    we fall back to today's price snapshot and upsert a single-day row per
    stale symbol. This keeps the nightly job's OHLCV coverage from drifting
    while the proper /uapi/.../inquire-daily-price client is being built.

    Failure mode: if KIS credentials / limiter / adapter blow up, raise so
    the stage is marked failed but subsequent stages still run.
    """
    from sqlalchemy import func, select

    from ky_adapters.kis.market import KISMarketAdapter
    from ky_core.storage import Repository
    from ky_core.storage.schema import OHLCV, Universe

    repo = Repository(owner_id="self")
    today_iso = date.today().isoformat()
    cutoff_iso = (date.today() - timedelta(days=KIS_STALE_BDAYS + 2)).isoformat()

    # Find universe rows whose latest OHLCV is older than cutoff (or missing).
    with repo.session() as sess:
        latest = (
            select(OHLCV.symbol, func.max(OHLCV.date).label("last_date"))
            .where(OHLCV.owner_id == repo.owner_id)
            .group_by(OHLCV.symbol)
            .subquery()
        )
        rows = (
            sess.execute(
                select(Universe.ticker, Universe.market, latest.c.last_date)
                .select_from(Universe.__table__.outerjoin(
                    latest, Universe.ticker == latest.c.symbol
                ))
                .where(Universe.owner_id == repo.owner_id)
                .where(Universe.is_etf.is_(False))
            )
            .all()
        )
    stale = [
        (r.ticker, r.market, r.last_date)
        for r in rows
        if r.last_date is None or r.last_date < cutoff_iso
    ]
    log.info(
        "KIS stale universe: %d/%d symbols need refresh (cutoff=%s)",
        len(stale), len(rows), cutoff_iso,
    )
    if not stale:
        return {"rows_added": 0, "symbols_processed": 0,
                "cutoff": cutoff_iso, "stale_total": 0}

    rows_added = 0
    processed = 0
    failed: list[str] = []

    # KIS finance rate limit is strict (~2 rps). We intentionally keep this
    # serial to respect the shared limiter + not stomp on the daytime API
    # budget. 2500 symbols ≈ ~20 minutes which fits inside the nightly window.
    market = KISMarketAdapter.from_settings()
    try:
        for ticker, mkt, _last in stale:
            try:
                snap = market.get_quote(ticker)  # current snapshot
            except Exception as exc:  # noqa: BLE001
                failed.append(f"{ticker}: {exc}")
                continue
            processed += 1
            try:
                close = float(snap.get("price") or 0) or None
                if close is None:
                    continue
                row = {
                    "symbol": ticker,
                    "market": mkt or "UNKNOWN",
                    "date": today_iso,
                    "open": _maybe_float(snap.get("open")),
                    "high": _maybe_float(snap.get("high")),
                    "low": _maybe_float(snap.get("low")),
                    "close": close,
                    "volume": _maybe_int(snap.get("volume")),
                    "adj_close": None,
                    "source_id": "kis",
                }
                rows_added += repo.upsert_ohlcv([row])
            except Exception as exc:  # noqa: BLE001
                failed.append(f"{ticker} upsert: {exc}")
    finally:
        try:
            market.close()
        except Exception:
            pass

    return {
        "rows_added": rows_added,
        "symbols_processed": processed,
        "stale_total": len(stale),
        "failed_count": len(failed),
        "failed_sample": failed[:5],
        "cutoff": cutoff_iso,
    }


def _maybe_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _maybe_int(v: Any) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# Stage 2 — FnGuide snapshot refresh                                          #
# --------------------------------------------------------------------------- #


def stage_fnguide_refresh() -> dict[str, Any]:
    """Refresh FnGuide / Naver snapshots older than 24h."""
    from datetime import timedelta as _td

    from sqlalchemy import select

    from ky_adapters.naver_fnguide import FnguideAdapter
    from ky_core.storage import Repository
    from ky_core.storage.schema import FnguideSnapshot, Universe

    repo = Repository(owner_id="self")
    cutoff = datetime.utcnow() - _td(hours=FNGUIDE_STALE_HOURS)

    with repo.session() as sess:
        uni = {
            (r.ticker, r.market): r.name
            for r in sess.execute(
                select(Universe.ticker, Universe.market, Universe.name)
                .where(Universe.owner_id == repo.owner_id)
                .where(Universe.is_etf.is_(False))
            ).all()
        }
        fresh = {
            r.symbol
            for r in sess.execute(
                select(FnguideSnapshot.symbol, FnguideSnapshot.fetched_at)
                .where(FnguideSnapshot.owner_id == repo.owner_id)
                .where(FnguideSnapshot.fetched_at >= cutoff)
            ).all()
        }

    stale_syms = [t for (t, _m) in uni.keys() if t not in fresh]
    stale_syms.sort()
    to_process = stale_syms[:FNGUIDE_MAX_SYMBOLS]
    log.info(
        "FnGuide stale: %d snapshots, processing %d (cap=%d)",
        len(stale_syms), len(to_process), FNGUIDE_MAX_SYMBOLS,
    )

    updated = 0
    failed: list[str] = []

    # Serial path — the adapter is network-bound but we want deterministic
    # logs for the nightly window. Parallel path lives in backfill_fnguide.py
    # if operators want to burst refresh manually.
    with FnguideAdapter.from_settings() as fng:
        for sym in to_process:
            try:
                snap = fng.get_full_snapshot(sym)
                if snap:
                    updated += 1
            except Exception as exc:  # noqa: BLE001
                failed.append(f"{sym}: {exc}")

    return {
        "rows_added": updated,
        "symbols_processed": len(to_process),
        "stale_total": len(stale_syms),
        "failed_count": len(failed),
        "failed_sample": failed[:5],
        "cutoff_utc": cutoff.isoformat(),
    }


# --------------------------------------------------------------------------- #
# Stage 3 — DART disclosures                                                  #
# --------------------------------------------------------------------------- #


def stage_dart_disclosures() -> dict[str, Any]:
    from ky_adapters.dart import DARTAdapter
    from ky_core.storage import Repository

    repo = Repository(owner_id="self")
    end = date.today()
    start = end - timedelta(days=DART_WINDOW_DAYS)

    with DARTAdapter.from_settings() as dart:
        filings = dart.list_disclosures(
            corp_code=None, start=start, end=end, page_count=100
        )
        rows = [f.as_row() for f in filings]
        written = repo.upsert_filings(rows) if rows else 0

    return {
        "rows_added": written,
        "symbols_processed": len({r.get("corp_code") for r in rows if r.get("corp_code")}),
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "filings_fetched": len(rows),
    }


# --------------------------------------------------------------------------- #
# Stage 4 — Macro refreshes                                                   #
# --------------------------------------------------------------------------- #


def stage_macro_refresh() -> dict[str, Any]:
    """Short-window macro pull — last 7 days by default."""
    import importlib.util

    from ky_core.storage import Repository
    from ky_core.storage.presets import ECOS_SERIES, EIA_SERIES, FRED_SERIES, KOSIS_SERIES

    # Load scripts/collect.py via spec — scripts/ is not a package.
    collect_path = ROOT / "scripts" / "collect.py"
    spec = importlib.util.spec_from_file_location("ky_collect", collect_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {collect_path}")
    collect_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collect_mod)

    repo = Repository(owner_id="self")
    end = date.today()
    start = end - timedelta(days=MACRO_WINDOW_DAYS)
    start_iso = start.isoformat()
    end_iso = end.isoformat()

    per_source: dict[str, dict[str, Any]] = {}
    total = 0

    def _run(tag: str, fn: Callable[[], int]) -> None:
        nonlocal total
        try:
            t = time.perf_counter()
            n = fn()
            per_source[tag] = {"rows": n, "duration_s": round(time.perf_counter() - t, 2)}
            total += n
        except Exception as exc:  # noqa: BLE001
            per_source[tag] = {"rows": 0, "error": f"{type(exc).__name__}: {exc}"}
            log.exception("macro/%s failed: %s", tag, exc)

    _run("fred", lambda: collect_mod.collect_fred(FRED_SERIES, start, end, repo))
    _run("ecos", lambda: collect_mod.collect_ecos(list(ECOS_SERIES), start_iso, end_iso, repo))
    _run("kosis", lambda: collect_mod.collect_kosis(KOSIS_SERIES, start_iso, end_iso, repo))
    _run("eia", lambda: collect_mod.collect_eia(EIA_SERIES, None, None, repo))
    _run("exim", lambda: collect_mod.collect_exim(repo))

    return {
        "rows_added": total,
        "symbols_processed": len(per_source),
        "window_start": start_iso,
        "window_end": end_iso,
        "per_source": per_source,
    }


# --------------------------------------------------------------------------- #
# Dispatch                                                                    #
# --------------------------------------------------------------------------- #


STAGE_FNS: dict[str, Callable[[], dict[str, Any]]] = {
    "kis_daily": stage_kis_daily,
    "fnguide_refresh": stage_fnguide_refresh,
    "dart_disclosures": stage_dart_disclosures,
    "macro_refresh": stage_macro_refresh,
}


def _parse_only(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    toks = [t.strip().lower() for t in raw.split(",") if t.strip()]
    # Accept short aliases too (e.g. "fred" hits macro_refresh).
    alias = {
        "kis": "kis_daily",
        "fnguide": "fnguide_refresh",
        "naver": "fnguide_refresh",
        "dart": "dart_disclosures",
        "macro": "macro_refresh",
        "fred": "macro_refresh",
        "ecos": "macro_refresh",
        "eia": "macro_refresh",
        "exim": "macro_refresh",
        "kosis": "macro_refresh",
    }
    out: list[str] = []
    for t in toks:
        key = alias.get(t, t)
        if key not in STAGE_FNS:
            raise SystemExit(f"unknown --only value: {t!r} (valid: {list(STAGE_FNS)})")
        if key not in out:
            out.append(key)
    return out


def _write_report(report: NightlyReport) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = OPS_DIR / f"nightly_run_{ts}.json"
    path.write_text(json.dumps(report.to_json(), indent=2), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ky-platform nightly data runner")
    p.add_argument("--dry-run", action="store_true",
                   help="list stages + config but skip execution")
    p.add_argument("--only", type=str, default=None,
                   help="comma-separated stage list (kis|fnguide|dart|fred|macro|…)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    log_path = _setup_logging()
    log.info("=" * 72)
    log.info("nightly start: %s", datetime.now(timezone.utc).isoformat())
    log.info("log file: %s", log_path)

    only = _parse_only(args.only)
    selected = only or list(STAGES)

    report = NightlyReport(
        started_at=datetime.now(timezone.utc).isoformat(),
        dry_run=args.dry_run,
        only=only,
        log_path=str(log_path),
    )

    t0 = time.perf_counter()
    for name in selected:
        fn = STAGE_FNS[name]
        res = _run_stage(name, fn, dry_run=args.dry_run)
        report.stages.append(res)
        report.total_rows_added += res.rows_added
        if res.status == "fail":
            report.errors.append(f"{name}: {res.error}")

    report.duration_s = round(time.perf_counter() - t0, 3)
    report.ended_at = datetime.now(timezone.utc).isoformat()
    ok_stages = sum(1 for s in report.stages if s.status in ("ok", "dry_run"))
    report.partial_success = bool(report.errors) and ok_stages > 0

    out_path = _write_report(report)
    log.info(
        "nightly done: rows=%d duration=%.2fs stages ok=%d/%d partial=%s → %s",
        report.total_rows_added,
        report.duration_s,
        ok_stages,
        len(report.stages),
        report.partial_success,
        out_path,
    )

    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
