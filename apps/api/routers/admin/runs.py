"""Nightly / weekly run-history endpoints, sourced from ~/.ky-platform/data/ops/."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from routers.admin._shared import OPS_DIR

router = APIRouter()


def _safe_load(path: Path) -> dict[str, Any] | None:
    """Read a run-report JSON tolerantly. Returns None on any corruption."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _summarise_run(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Trim a full report down to what the UI needs for the history table."""
    stages = payload.get("stages") or []
    ok_count = sum(1 for s in stages if s.get("status") in ("ok", "dry_run"))
    fail = sum(1 for s in stages if s.get("status") == "fail")
    return {
        "file": path.name,
        "kind": payload.get("kind", "nightly"),
        "started_at": payload.get("started_at"),
        "ended_at": payload.get("ended_at"),
        "duration_s": payload.get("duration_s", 0.0),
        "total_rows_added": payload.get("total_rows_added", 0),
        "stage_count": len(stages),
        "stage_ok": ok_count,
        "stage_fail": fail,
        "partial_success": bool(payload.get("partial_success")),
        "dry_run": bool(payload.get("dry_run")),
        "errors": payload.get("errors") or [],
        "stages": [
            {
                "name": s.get("name"),
                "status": s.get("status"),
                "duration_s": s.get("duration_s", 0.0),
                "rows_added": s.get("rows_added", 0),
                "symbols_processed": s.get("symbols_processed", 0),
                "error": s.get("error"),
            }
            for s in stages
        ],
    }


def _load_runs(kind: str, limit: int) -> list[dict[str, Any]]:
    prefix = f"{kind}_run_"
    if not OPS_DIR.exists():
        return []
    files = sorted(
        (p for p in OPS_DIR.glob(f"{prefix}*.json") if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:limit]
    out: list[dict[str, Any]] = []
    for p in files:
        payload = _safe_load(p)
        if payload is None:
            out.append({
                "file": p.name,
                "kind": kind,
                "error": "unreadable report file",
                "started_at": datetime.fromtimestamp(
                    p.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
            })
            continue
        out.append(_summarise_run(p, payload))
    return out


@router.get("/nightly_runs")
def nightly_runs(
    limit: int = Query(default=7, ge=1, le=365),
) -> dict:
    """Recent nightly-run reports from ~/.ky-platform/data/ops/.

    Default limit is 7 (one week of daily runs). The Admin/Pipeline page
    passes ``limit=30`` for a broader history view.
    """
    try:
        runs = _load_runs("nightly", limit)
        warning: str | None = None
        if not OPS_DIR.exists():
            warning = f"ops dir missing: {OPS_DIR}"
        return {
            "ok": True,
            "data": {
                "root": str(OPS_DIR),
                "kind": "nightly",
                "limit": limit,
                "runs": runs,
                "warning": warning,
            },
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "data": None,
            "error": {"code": "NIGHTLY_RUNS_READ", "message": str(exc)},
        }


@router.get("/weekly_runs")
def weekly_runs(
    limit: int = Query(default=7, ge=1, le=104),
) -> dict:
    """Recent weekly-run reports. Symmetric to /nightly_runs."""
    try:
        runs = _load_runs("weekly", limit)
        warning: str | None = None
        if not OPS_DIR.exists():
            warning = f"ops dir missing: {OPS_DIR}"
        return {
            "ok": True,
            "data": {
                "root": str(OPS_DIR),
                "kind": "weekly",
                "limit": limit,
                "runs": runs,
                "warning": warning,
            },
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "data": None,
            "error": {"code": "WEEKLY_RUNS_READ", "message": str(exc)},
        }
