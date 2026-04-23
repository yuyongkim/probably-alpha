#!/usr/bin/env python
"""Weekly data-maintenance runner for ky-platform.

Scheduled Sunday 04:00 KST. Slower, broader passes that don't belong in the
nightly window:

  1. Legacy macro refresh        — re-import any stale legacy CSVs.
  2. Moat v2 universe recompute  — derived metric recompute (Piotroski deps).
  3. Piotroski + Altman full pass — every tradable symbol.
  4. Factor IC update            — recompute factor information coefficients.
  5. RAG index rebuild           — only when new PDFs present.

Stage failures are logged to the run report but do NOT abort later stages.

Reports land next to nightly reports::

    ~/.ky-platform/data/ops/weekly_run_<UTC_YYYYMMDD_HHMMSS>.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
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

STAGES = (
    "legacy_macro_refresh",
    "moat_v2_recompute",
    "piotroski_altman_full",
    "factor_ic_update",
    "rag_index_rebuild",
)


def _setup_logging() -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"weekly_{ts}.log"
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


log = logging.getLogger("weekly")


@dataclass
class StageResult:
    name: str
    status: str = "pending"
    started_at: str | None = None
    ended_at: str | None = None
    duration_s: float = 0.0
    rows_added: int = 0
    symbols_processed: int = 0
    error: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class WeeklyReport:
    kind: str = "weekly"
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
        return asdict(self)


# --------------------------------------------------------------------------- #
# Stage helpers                                                               #
# --------------------------------------------------------------------------- #


def _run_stage(name: str, fn: Callable[[], dict[str, Any]], *, dry_run: bool) -> StageResult:
    res = StageResult(name=name)
    if dry_run:
        res.status = "dry_run"
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
        log.info("[%s] ok rows=%d symbols=%d", name, res.rows_added, res.symbols_processed)
    except Exception as exc:  # noqa: BLE001
        res.status = "fail"
        res.error = f"{type(exc).__name__}: {exc}"
        log.exception("[%s] FAILED: %s", name, exc)
    finally:
        res.ended_at = datetime.now(timezone.utc).isoformat()
        res.duration_s = round(time.perf_counter() - t0, 3)
    return res


# --------------------------------------------------------------------------- #
# Stages                                                                      #
# --------------------------------------------------------------------------- #


def stage_legacy_macro_refresh() -> dict[str, Any]:
    """Re-import legacy macro CSVs if the backfill script is present.

    ``scripts/import_legacy_macro.py`` is the authoritative importer; this
    stage runs the equivalent in-process. If the script isn't importable we
    skip gracefully rather than failing the run.
    """
    import importlib.util

    script = ROOT / "scripts" / "import_legacy_macro.py"
    if not script.exists():
        return {"rows_added": 0, "note": "import_legacy_macro.py not present — skipping"}
    spec = importlib.util.spec_from_file_location("ky_legacy_macro", script)
    if spec is None or spec.loader is None:
        return {"rows_added": 0, "note": "cannot load import_legacy_macro.py"}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Expected interface: mod.main(argv) -> int. If absent, note + return.
    main_fn = getattr(mod, "main", None)
    if main_fn is None:
        return {"rows_added": 0, "note": "import_legacy_macro has no main()"}
    rc = main_fn([])  # type: ignore[misc]
    return {"rows_added": 0, "exit_code": int(rc or 0)}


def stage_moat_v2_recompute() -> dict[str, Any]:
    """Recompute Moat v2 derived metrics across the universe.

    Delegates to the core recompute helper if available; otherwise returns
    a no-op stub so the stage doesn't fail the run before the helper lands.
    """
    try:
        from ky_core.value.moat import recompute_moat_v2_all  # type: ignore
    except Exception:
        return {"rows_added": 0, "note": "ky_core.value.moat.recompute_moat_v2_all not present"}
    n = int(recompute_moat_v2_all())
    return {"rows_added": n, "symbols_processed": n}


def stage_piotroski_altman_full() -> dict[str, Any]:
    """Full-universe Piotroski 9 + Altman 5 recompute."""
    updated = 0
    notes: list[str] = []
    try:
        from ky_core.value.piotroski import recompute_piotroski_all  # type: ignore
        updated += int(recompute_piotroski_all())
    except Exception as exc:  # noqa: BLE001
        notes.append(f"piotroski: {exc}")
    try:
        from ky_core.value.altman import recompute_altman_all  # type: ignore
        updated += int(recompute_altman_all())
    except Exception as exc:  # noqa: BLE001
        notes.append(f"altman: {exc}")
    return {"rows_added": updated, "notes": notes}


def stage_factor_ic_update() -> dict[str, Any]:
    """Recompute factor ICs. Skips cleanly if helper not present."""
    try:
        from ky_core.quant.factor_ic import recompute_factor_ic  # type: ignore
    except Exception:
        return {"rows_added": 0, "note": "ky_core.quant.factor_ic.recompute_factor_ic not present"}
    n = int(recompute_factor_ic())
    return {"rows_added": n}


def stage_rag_index_rebuild() -> dict[str, Any]:
    """Rebuild the RAG index if the docs directory has new files."""
    import importlib.util

    rag_dir = Path.home() / ".ky-platform" / "data" / "rag"
    docs_dir = ROOT / "docs"
    # Detect "new-ness" by comparing mtimes. Missing index → rebuild.
    index_marker = rag_dir / "index.json"
    if index_marker.exists() and docs_dir.exists():
        idx_mtime = index_marker.stat().st_mtime
        newest = max(
            (p.stat().st_mtime for p in docs_dir.rglob("*") if p.is_file()),
            default=0.0,
        )
        if newest <= idx_mtime:
            return {"rows_added": 0, "note": "RAG index up-to-date — skipping"}

    script = ROOT / "scripts" / "build_rag.py"
    if not script.exists():
        return {"rows_added": 0, "note": "build_rag.py not present"}
    spec = importlib.util.spec_from_file_location("ky_build_rag", script)
    if spec is None or spec.loader is None:
        return {"rows_added": 0, "note": "cannot load build_rag.py"}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    main_fn = getattr(mod, "main", None)
    if main_fn is None:
        return {"rows_added": 0, "note": "build_rag has no main()"}
    rc = main_fn([])  # type: ignore[misc]
    return {"rows_added": 0, "exit_code": int(rc or 0)}


STAGE_FNS: dict[str, Callable[[], dict[str, Any]]] = {
    "legacy_macro_refresh": stage_legacy_macro_refresh,
    "moat_v2_recompute": stage_moat_v2_recompute,
    "piotroski_altman_full": stage_piotroski_altman_full,
    "factor_ic_update": stage_factor_ic_update,
    "rag_index_rebuild": stage_rag_index_rebuild,
}


def _parse_only(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    toks = [t.strip().lower() for t in raw.split(",") if t.strip()]
    alias = {
        "macro": "legacy_macro_refresh",
        "moat": "moat_v2_recompute",
        "piotroski": "piotroski_altman_full",
        "altman": "piotroski_altman_full",
        "ic": "factor_ic_update",
        "factor": "factor_ic_update",
        "rag": "rag_index_rebuild",
    }
    out: list[str] = []
    for t in toks:
        key = alias.get(t, t)
        if key not in STAGE_FNS:
            raise SystemExit(f"unknown --only value: {t!r} (valid: {list(STAGE_FNS)})")
        if key not in out:
            out.append(key)
    return out


def _write_report(report: WeeklyReport) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = OPS_DIR / f"weekly_run_{ts}.json"
    path.write_text(json.dumps(report.to_json(), indent=2), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ky-platform weekly data runner")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--only", type=str, default=None,
                   help="comma-separated stage list (macro|moat|piotroski|ic|rag|…)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    log_path = _setup_logging()
    log.info("=" * 72)
    log.info("weekly start: %s", datetime.now(timezone.utc).isoformat())
    log.info("log file: %s", log_path)

    only = _parse_only(args.only)
    selected = only or list(STAGES)

    report = WeeklyReport(
        started_at=datetime.now(timezone.utc).isoformat(),
        dry_run=args.dry_run,
        only=only,
        log_path=str(log_path),
    )

    t0 = time.perf_counter()
    for name in selected:
        res = _run_stage(name, STAGE_FNS[name], dry_run=args.dry_run)
        report.stages.append(res)
        report.total_rows_added += res.rows_added
        if res.status == "fail":
            report.errors.append(f"{name}: {res.error}")

    report.duration_s = round(time.perf_counter() - t0, 3)
    report.ended_at = datetime.now(timezone.utc).isoformat()
    ok_stages = sum(1 for s in report.stages if s.status in ("ok", "dry_run"))
    report.partial_success = bool(report.errors) and ok_stages > 0

    out = _write_report(report)
    log.info(
        "weekly done: rows=%d duration=%.2fs ok=%d/%d partial=%s → %s",
        report.total_rows_added,
        report.duration_s,
        ok_stages,
        len(report.stages),
        report.partial_success,
        out,
    )
    return 0 if not report.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
