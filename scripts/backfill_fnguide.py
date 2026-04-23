#!/usr/bin/env python
"""Bulk FnGuide / Naver snapshot backfill.

Walks the live-validated universe (KOSPI + KOSDAQ, non-ETF) and refreshes
each symbol's enriched FnGuide snapshot via ``FnguideAdapter.get_full_snapshot``.
The adapter's DB-first cache means this script is idempotent — re-running
only refreshes rows older than 24h.

Usage
-----
    # full run (all KOSPI+KOSDAQ non-ETF symbols, ~2 workers, 1.5s/symbol)
    python scripts/backfill_fnguide.py

    # subset — first 200 symbols (smoke test)
    python scripts/backfill_fnguide.py --batch 200

    # start from symbol 1000, process 500
    python scripts/backfill_fnguide.py --offset 1000 --batch 500

    # skip ones already fresh < 7 days old
    python scripts/backfill_fnguide.py --skip-fresh-days 7

The runner writes a per-run log under ``runtime_logs/backfill_fnguide_<UTC>.log``
and reports progress every 1% of the universe.

Why it matters
--------------
Pre-run state (2026-04-22): 102 ``live_fresh`` snapshots (rich payloads with
Mobile integration + NaverComp cF3002/cF4002/cF9001 + investor_trend) vs
2,421 stale rows imported from the legacy Company_Credit DB. This script
grows the live cohort toward the full 2,500+ universe so sector-rotation and
leader-stock scoring work against fresh data.
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ---- make sibling packages importable ---- #
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "packages" / "adapters", ROOT / "packages" / "core"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import json

from ky_adapters.naver_fnguide import FnguideAdapter
from ky_core.storage import Repository
from ky_core.storage.schema import Universe, FnguideSnapshot

LOG_DIR = ROOT / "runtime_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

STOP_EVENT = threading.Event()


def _setup_logging() -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"backfill_fnguide_{ts}.log"
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
    # Mute noisy httpx request-level logs; keep warnings
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return log_path


log = logging.getLogger("backfill_fnguide")


# --------------------------------------------------------------------------- #
# Universe scan                                                               #
# --------------------------------------------------------------------------- #


@dataclass
class Stats:
    total: int = 0
    attempted: int = 0
    success: int = 0
    failures: int = 0
    already_fresh: int = 0
    per_source: dict[str, int] = field(default_factory=dict)
    failed_symbols: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "attempted": self.attempted,
            "success": self.success,
            "failures": self.failures,
            "already_fresh": self.already_fresh,
            "per_source": self.per_source,
            "failed_sample": self.failed_symbols[:30],
        }


def _load_universe(repo: Repository) -> list[str]:
    """Return KRX symbols: KOSPI + KOSDAQ, non-ETF, sorted ascending."""
    with repo.session() as sess:
        rows = (
            sess.query(Universe.ticker)
            .filter(
                Universe.owner_id == repo.owner_id,
                Universe.market.in_(["KOSPI", "KOSDAQ"]),
                Universe.is_etf.is_(False),
            )
            .order_by(Universe.ticker.asc())
            .all()
        )
    # Normalise to 6-digit numeric KRX symbol
    out = []
    for (ticker,) in rows:
        if not ticker:
            continue
        digits = "".join(c for c in str(ticker) if c.isdigit())
        if len(digits) == 6:
            out.append(digits)
    return out


def _fresh_symbols(repo: Repository, max_age_days: float) -> set[str]:
    """Symbols whose snapshot is live_fresh AND younger than the cutoff."""
    cutoff = datetime.utcnow() - timedelta(days=max_age_days)
    with repo.session() as sess:
        rows = (
            sess.query(FnguideSnapshot.symbol, FnguideSnapshot.fetched_at, FnguideSnapshot.source)
            .filter(
                FnguideSnapshot.owner_id == repo.owner_id,
                FnguideSnapshot.fetched_at >= cutoff,
                FnguideSnapshot.source.in_(["live_fresh", "mixed", "naver_mobile"]),
            )
            .all()
        )
    return {sym for (sym, _, _) in rows}


# --------------------------------------------------------------------------- #
# Worker                                                                      #
# --------------------------------------------------------------------------- #


def _refresh_one(
    symbol: str, rate_limit_sec: float, max_retries: int = 3
) -> tuple[str, str | None, str | None]:
    """Fetch + persist one symbol's snapshot. Returns (symbol, source, error).

    Sleeps ``rate_limit_sec`` after the upstream call to stay polite with
    Naver / WiseReport. Retries on transient errors with exponential backoff.
    """
    last_err: str | None = None
    for attempt in range(max_retries):
        if STOP_EVENT.is_set():
            return symbol, None, "aborted"
        try:
            adapter = FnguideAdapter.from_settings()
            try:
                snap = adapter.get_full_snapshot(symbol)
            finally:
                adapter.close()
            source = snap.source
            # The adapter persists live_fresh/naver_mobile internally; we
            # still upsert here as belt-and-braces for flaky runs.
            if source in ("live_fresh", "naver_mobile", "mixed") and not snap.degraded:
                try:
                    Repository().upsert_fnguide_snapshot(
                        symbol,
                        json.dumps(snap.to_dict(), ensure_ascii=False),
                        source=source,
                        degraded=snap.degraded,
                    )
                except Exception as exc:  # noqa: BLE001
                    last_err = f"persist: {exc}"
            time.sleep(rate_limit_sec)
            return symbol, source, None
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}: {exc}"
            backoff = 1.5 * (2**attempt)
            time.sleep(min(backoff, 8.0))
    return symbol, None, last_err


# --------------------------------------------------------------------------- #
# Entrypoint                                                                  #
# --------------------------------------------------------------------------- #


def _install_signal_handlers() -> None:
    def _handler(signum, _frame):  # noqa: ARG001
        log.warning("signal %s received — draining in-flight requests…", signum)
        STOP_EVENT.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handler)
        except (ValueError, AttributeError):
            # SIGTERM unavailable on Windows main thread
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bulk FnGuide snapshot backfill.")
    parser.add_argument("--workers", type=int, default=5,
                        help="Max concurrent workers. Default 5 — Naver/WiseReport"
                             " rate-limit beyond this.")
    parser.add_argument("--rate-limit-sec", type=float, default=1.5,
                        help="Per-call sleep (s) to stay polite. Default 1.5s.")
    parser.add_argument("--batch", type=int, default=0,
                        help="Limit work to the first N symbols (0 = all).")
    parser.add_argument("--offset", type=int, default=0,
                        help="Skip the first N symbols (useful for resume).")
    parser.add_argument("--skip-fresh-days", type=float, default=1.0,
                        help="Skip symbols whose live_fresh row is younger "
                             "than this many days. Default 1.0.")
    parser.add_argument("--owner-id", type=str, default="self")
    parser.add_argument("--dry-run", action="store_true",
                        help="List candidate symbols and exit.")
    args = parser.parse_args(argv)

    log_path = _setup_logging()
    _install_signal_handlers()

    log.info("=" * 72)
    log.info("fnguide bulk backfill start: %s", datetime.utcnow().isoformat())
    log.info("log file: %s", log_path)

    repo = Repository(owner_id=args.owner_id)
    universe = _load_universe(repo)
    fresh = _fresh_symbols(repo, args.skip_fresh_days)
    candidates = [s for s in universe if s not in fresh]

    log.info(
        "universe=%d, already_fresh=%d, candidates=%d",
        len(universe), len(fresh), len(candidates),
    )

    if args.offset > 0:
        candidates = candidates[args.offset:]
        log.info("offset applied — candidates now %d", len(candidates))
    if args.batch > 0:
        candidates = candidates[: args.batch]
        log.info("batch applied — candidates now %d", len(candidates))

    if args.dry_run:
        log.info("dry-run — first 20 candidates: %s", candidates[:20])
        return 0

    stats = Stats(total=len(candidates), already_fresh=len(fresh))
    progress_every = max(1, len(candidates) // 100)  # 1 % resolution
    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(_refresh_one, sym, args.rate_limit_sec): sym
            for sym in candidates
        }
        for n, fut in enumerate(as_completed(futures), 1):
            sym = futures[fut]
            try:
                symbol, source, error = fut.result()
            except Exception as exc:  # noqa: BLE001
                symbol, source, error = sym, None, f"unhandled: {exc}"
            stats.attempted += 1
            if error:
                stats.failures += 1
                stats.failed_symbols.append((symbol, error))
                if stats.failures <= 10:
                    log.warning("%-6s FAIL: %s", symbol, error)
            else:
                stats.success += 1
                stats.per_source[source or "?"] = stats.per_source.get(source or "?", 0) + 1
            if n % progress_every == 0 or n == len(candidates):
                elapsed = time.perf_counter() - t0
                rate = n / elapsed if elapsed > 0 else 0.0
                eta = (len(candidates) - n) / rate if rate > 0 else 0.0
                pct = 100.0 * n / len(candidates)
                log.info(
                    "progress %5.1f%% (%d/%d) ok=%d fail=%d  rate=%.1f sym/s  eta=%.0fs",
                    pct, n, len(candidates),
                    stats.success, stats.failures, rate, eta,
                )
            if STOP_EVENT.is_set():
                log.warning("shutting down — cancelling remaining futures")
                for f in futures:
                    f.cancel()
                break

    elapsed = time.perf_counter() - t0
    log.info("=" * 72)
    log.info("backfill done in %.1fs", elapsed)
    log.info("result: %s", json.dumps(stats.to_dict(), ensure_ascii=False, indent=2))

    # Final DB counts — what actually stuck (background refreshers continue
    # writing even after our futures resolve, so a fresh snapshot is more
    # reliable than our in-memory counter).
    with repo.session() as sess:
        live = (
            sess.query(FnguideSnapshot)
            .filter(
                FnguideSnapshot.owner_id == repo.owner_id,
                FnguideSnapshot.source.in_(["live_fresh", "mixed", "naver_mobile"]),
            )
            .count()
        )
        total = (
            sess.query(FnguideSnapshot)
            .filter(FnguideSnapshot.owner_id == repo.owner_id)
            .count()
        )
    log.info("DB state: total_snapshots=%d, live_fresh_family=%d", total, live)
    return 0 if stats.failures < stats.total / 2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
