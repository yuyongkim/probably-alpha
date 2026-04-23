"""Chartist backtest endpoints — list / read / run real-data backtests.

All runs live on disk at ``~/.ky-platform/data/backtest/run_<id>.json``.
The UI fetches either:

    GET /api/v1/chartist/backtest/list           — index of all runs
    GET /api/v1/chartist/backtest?run_id=...     — single run artefact
    GET /api/v1/chartist/backtest?strategy=sepa  — latest run for strategy
    POST /api/v1/chartist/backtest/run           — kick off a new run

The POST is admin-only in spirit (no auth plumbing yet, but the CORS
origin already restricts to localhost during dev).
"""
from __future__ import annotations

import json
import logging
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

logger = logging.getLogger(__name__)
router = APIRouter()

BACKTEST_DIR = Path.home() / ".ky-platform" / "data" / "backtest"

_RUN_STATE: dict[str, dict[str, Any]] = {}   # run_id → status


def _envelope(data: Any = None, error: Any = None, ok: bool | None = None) -> dict:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}


# --------------------------------------------------------------------------- #
# List                                                                        #
# --------------------------------------------------------------------------- #


@router.get("/list")
def list_runs(limit: int = Query(default=50, ge=1, le=200)) -> dict:
    """Return a compact index of all saved backtest runs, newest first."""
    if not BACKTEST_DIR.exists():
        return _envelope({"runs": [], "count": 0})
    rows: list[dict[str, Any]] = []
    for path in sorted(BACKTEST_DIR.glob("run_*.json"), reverse=True)[:limit]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("skip bad run file %s: %s", path, exc)
            continue
        cfg = data.get("config", {})
        m = data.get("metrics", {})
        rows.append({
            "run_id": data.get("run_id", path.stem.replace("run_", "")),
            "strategy": cfg.get("strategy_name"),
            "start": cfg.get("start"),
            "end": cfg.get("end"),
            "generated_at": data.get("generated_at"),
            "universe_size": data.get("universe_size"),
            "n_trades": m.get("n_trades", 0),
            "cagr": m.get("cagr", 0.0),
            "max_drawdown": m.get("max_drawdown", 0.0),
            "sharpe": m.get("sharpe", 0.0),
            "win_rate": m.get("win_rate", 0.0),
            "final_equity": m.get("final_equity", 0.0),
            "total_return": m.get("total_return", 0.0),
            "path": path.name,
        })
    return _envelope({"count": len(rows), "runs": rows})


# --------------------------------------------------------------------------- #
# Read single run                                                             #
# --------------------------------------------------------------------------- #


@router.get("")
def get_run(
    run_id: str | None = Query(default=None),
    strategy: str | None = Query(default=None),
    trim_curve: int = Query(default=0, ge=0, le=5000,
                            description="If >0, equity curve is downsampled to this length"),
) -> dict:
    """Return a single run's artefact.

    Either ``run_id`` (exact) or ``strategy`` (latest for that strategy) must
    be provided. When both are empty we return the absolute latest run.
    """
    path = _resolve_run_path(run_id=run_id, strategy=strategy)
    if path is None:
        raise HTTPException(status_code=404, detail="no matching backtest run found")
    data = json.loads(path.read_text(encoding="utf-8"))
    if trim_curve and len(data.get("equity_curve", [])) > trim_curve:
        data["equity_curve"] = _downsample(data["equity_curve"], trim_curve)
        data["benchmark_curve"] = _downsample(data.get("benchmark_curve", []), trim_curve)
    return _envelope(data)


def _resolve_run_path(*, run_id: str | None, strategy: str | None) -> Path | None:
    if not BACKTEST_DIR.exists():
        return None
    if run_id:
        # accept run_id with or without the "run_" prefix
        name = run_id if run_id.startswith("run_") else f"run_{run_id}"
        p = BACKTEST_DIR / f"{name}.json"
        return p if p.exists() else None
    candidates = sorted(BACKTEST_DIR.glob("run_*.json"), reverse=True)
    if strategy:
        for path in candidates:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data.get("config", {}).get("strategy_name") == strategy:
                return path
        return None
    return candidates[0] if candidates else None


def _downsample(points: list[dict[str, Any]], target: int) -> list[dict[str, Any]]:
    if not points or len(points) <= target:
        return points
    step = max(1, len(points) // target)
    out = points[::step]
    if out[-1] is not points[-1]:
        out.append(points[-1])
    return out


# --------------------------------------------------------------------------- #
# Trigger new run                                                             #
# --------------------------------------------------------------------------- #


class RunRequest(BaseModel):
    strategy: str = Field(..., description="sepa | magic_formula | quality_momentum | value_qmj")
    start: str = Field(..., description="ISO YYYY-MM-DD")
    end: str = Field(..., description="ISO YYYY-MM-DD")
    initial_cash: float = 100_000_000.0
    max_positions: int = 10
    stop_loss_pct: float = 0.07
    risk_per_trade_pct: float = 0.02


@router.post("/run")
def trigger_run(req: RunRequest, background: BackgroundTasks) -> dict:
    """Queue a backtest run. Returns a pending run_id the caller can poll
    via GET /api/v1/chartist/backtest?run_id=...
    """
    from ky_core.backtest.strategies import REGISTRY

    if req.strategy not in REGISTRY:
        raise HTTPException(status_code=400, detail=f"unknown strategy: {req.strategy}")

    pending_id = datetime.utcnow().strftime("pending_%Y%m%d_%H%M%S")
    _RUN_STATE[pending_id] = {
        "pending_id": pending_id,
        "status": "QUEUED",
        "strategy": req.strategy,
        "queued_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    background.add_task(_execute_run, pending_id, req.model_dump())
    return _envelope({"pending_id": pending_id, "status": "QUEUED"})


@router.get("/run/status")
def run_status(pending_id: str) -> dict:
    state = _RUN_STATE.get(pending_id)
    if state is None:
        raise HTTPException(status_code=404, detail="unknown pending_id")
    return _envelope(state)


def _execute_run(pending_id: str, payload: dict[str, Any]) -> None:
    from ky_core.backtest import BacktestConfig, BacktestEngine
    from ky_core.backtest.strategies import build as build_strategy

    state = _RUN_STATE[pending_id]
    state.update({"status": "RUNNING",
                  "started_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"})
    try:
        cfg = BacktestConfig(
            strategy_name=payload["strategy"],
            start=payload["start"],
            end=payload["end"],
            initial_cash=payload.get("initial_cash", 100_000_000.0),
            max_positions=payload.get("max_positions", 10),
            stop_loss_pct=payload.get("stop_loss_pct", 0.07),
            risk_per_trade_pct=payload.get("risk_per_trade_pct", 0.02),
        )
        strat = build_strategy(payload["strategy"])
        engine = BacktestEngine(cfg)
        run = engine.run(strat)
        path = engine.save(run)
        state.update({
            "status": "DONE",
            "run_id": run.run_id,
            "path": str(path),
            "finished_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "metrics": run.metrics.to_dict(),
        })
    except Exception as exc:
        logger.exception("backtest run failed")
        state.update({
            "status": "FAILED",
            "error": f"{type(exc).__name__}: {exc}",
            "finished_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        })
