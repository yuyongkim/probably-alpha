"""Admin router — 상태 / 잡 / 감사 로그 / 시크릿 존재 여부 / 테넌트 관리."""
from __future__ import annotations

import json
import logging
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query

# Make packages/core importable (mirrors routers/chartist bootstrap).
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

from ky_core.storage.repository import Repository  # noqa: E402

from config import settings  # noqa: E402
from middleware.auth import hash_api_key  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter()

# Reports land here via scripts/nightly.py and scripts/weekly.py.
# Mirrored as a constant so the frontend can show the origin path.
OPS_DIR = Path.home() / ".ky-platform" / "data" / "ops"


# --------------------------------------------------------------------------- #
# Envelope helpers shared with the tenant / usage / audit endpoints           #
# --------------------------------------------------------------------------- #


def _ok(data: Any) -> dict:
    return {"ok": True, "data": data, "error": None}


def _err(code: str, message: str, *, detail: dict | None = None) -> dict:
    return {
        "ok": False,
        "data": None,
        "error": {"code": code, "message": message, "detail": detail or {}},
    }


def _require_admin(header_value: str | None) -> None:
    """Gate mutating endpoints. When ``KY_ADMIN_TOKEN`` is unset ALL mutations
    are refused — we never silently open up the control plane."""
    token = settings.ky_admin_token
    if not token:
        raise HTTPException(status_code=403, detail="KY_ADMIN_TOKEN is not configured")
    if header_value != token:
        raise HTTPException(status_code=401, detail="invalid admin token")


def _is_admin(header_value: str | None) -> bool:
    token = settings.ky_admin_token
    return bool(token) and header_value == token


def _public_tenant(row: dict[str, Any]) -> dict[str, Any]:
    """Never return the api_key_hash over the wire."""
    return {k: v for k, v in row.items() if k != "api_key_hash"}


@router.get("/status")
def admin_status() -> dict:
    """Returns service + secret-presence status. Never returns secret values."""
    return {
        "ok": True,
        "data": {
            "owner_id": settings.platform_owner_id,
            "shared_env_loaded": settings.shared_env_present,
            "admin_token_configured": bool(settings.ky_admin_token),
            "secrets_present": {
                "kis": bool(settings.kis_app_key and settings.kis_app_secret),
                "kiwoom": bool(settings.kiwoom_app_key and settings.kiwoom_secret_key),
                "dart": bool(settings.dart_api_key),
                "fred": bool(settings.fred_api_key),
                "ecos": bool(settings.ecos_api_key),
            },
            "feature_flags": {
                "stock_modal": settings.enable_stock_modal,
                "ticker_tape": settings.enable_ticker_tape,
            },
        },
        "error": None,
    }


# --------------------------------------------------------------------------- #
# Tenants — CRUD                                                              #
# --------------------------------------------------------------------------- #


@router.get("/tenants")
def list_tenants(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    """List tenants. GET is allowed without an admin token, but a non-admin
    caller only ever sees the ``self`` row — matching the spec's default."""
    repo = Repository()
    repo.ensure_self_tenant()
    if _is_admin(x_admin_token):
        rows = repo.list_tenants()
    else:
        self_row = repo.get_tenant("self")
        rows = [self_row] if self_row else []
    return _ok({"count": len(rows), "tenants": [_public_tenant(r) for r in rows]})


@router.post("/tenants")
def create_tenant(
    payload: dict,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    _require_admin(x_admin_token)

    tenant_id = (payload.get("tenant_id") or "").strip()
    display_name = (payload.get("display_name") or tenant_id).strip()
    plan = (payload.get("plan") or "trial").strip()
    rate_limit = int(payload.get("rate_limit_per_min") or _plan_default_rate(plan))
    enabled = bool(payload.get("enabled", True))
    if not tenant_id or not tenant_id.replace("_", "").replace("-", "").isalnum():
        return _err("INVALID_TENANT_ID", "tenant_id must be alphanumeric (- and _ allowed)")
    if tenant_id == "self":
        return _err("RESERVED", "'self' is reserved for the built-in tenant")

    repo = Repository()
    repo.ensure_self_tenant()
    if repo.get_tenant(tenant_id):
        return _err("ALREADY_EXISTS", f"tenant '{tenant_id}' already exists")

    api_key = _generate_api_key(tenant_id)
    row = repo.upsert_tenant(
        tenant_id=tenant_id,
        display_name=display_name,
        api_key_hash=hash_api_key(api_key),
        plan=plan,
        rate_limit_per_min=rate_limit,
        enabled=enabled,
    )
    repo.log_audit(
        tenant_id="self",
        action="tenant_created",
        detail=json.dumps({"target": tenant_id, "plan": plan}),
    )
    # api_key is returned ONCE — caller must persist it client-side.
    return _ok({"tenant": _public_tenant(row), "api_key": api_key})


@router.post("/tenants/{tenant_id}/rotate")
def rotate_tenant_key(
    tenant_id: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    _require_admin(x_admin_token)
    if tenant_id == "self":
        return _err("RESERVED", "cannot rotate key for the built-in 'self' tenant")
    repo = Repository()
    api_key = _generate_api_key(tenant_id)
    row = repo.rotate_tenant_api_key(tenant_id, hash_api_key(api_key))
    if row is None:
        return _err("NOT_FOUND", f"tenant '{tenant_id}' not found")
    repo.log_audit(
        tenant_id="self",
        action="tenant_key_rotated",
        detail=json.dumps({"target": tenant_id}),
    )
    return _ok({"tenant": _public_tenant(row), "api_key": api_key})


@router.delete("/tenants/{tenant_id}")
def disable_tenant(
    tenant_id: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    _require_admin(x_admin_token)
    if tenant_id == "self":
        return _err("RESERVED", "cannot disable the built-in 'self' tenant")
    repo = Repository()
    row = repo.set_tenant_enabled(tenant_id, False)
    if row is None:
        return _err("NOT_FOUND", f"tenant '{tenant_id}' not found")
    repo.log_audit(
        tenant_id="self",
        action="tenant_disabled",
        detail=json.dumps({"target": tenant_id}),
    )
    return _ok({"tenant": _public_tenant(row)})


# --------------------------------------------------------------------------- #
# Usage + billing                                                             #
# --------------------------------------------------------------------------- #


@router.get("/usage")
def usage(
    tenant_id: str | None = Query(default=None),
    since_hours: int = Query(default=24, ge=1, le=24 * 30),
    limit: int = Query(default=200, ge=1, le=2000),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    repo = Repository()
    since = datetime.utcnow() - timedelta(hours=since_hours)
    # Non-admin callers are locked to the 'self' tenant.
    scoped = tenant_id if _is_admin(x_admin_token) else "self"
    rows = repo.list_api_usage(tenant_id=scoped, since=since, limit=limit)
    summary = repo.usage_summary_by_tenant(since=since)
    if not _is_admin(x_admin_token):
        summary = [s for s in summary if s["tenant_id"] == "self"]
    # Dummy pricing: self 0 / trial 0 / pro $100/mo / enterprise $500/mo
    tenant_rows = {t["tenant_id"]: t for t in repo.list_tenants()}
    for s in summary:
        plan = tenant_rows.get(s["tenant_id"], {}).get("plan", "self")
        s["plan"] = plan
        s["monthly_fee_usd"] = _plan_price(plan)
    return _ok(
        {
            "since": since.isoformat() + "Z",
            "summary": summary,
            "events": rows,
        }
    )


@router.get("/audit")
def audit(
    tenant_id: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=2000),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    repo = Repository()
    scoped = tenant_id if _is_admin(x_admin_token) else "self"
    rows = repo.list_audit(tenant_id=scoped, limit=limit)
    return _ok({"count": len(rows), "events": rows})


# --------------------------------------------------------------------------- #
# Plan helpers                                                                #
# --------------------------------------------------------------------------- #


def _plan_default_rate(plan: str) -> int:
    return {
        "self": 9999,
        "trial": 30,
        "pro": 300,
        "enterprise": 1200,
    }.get(plan, 60)


def _plan_price(plan: str) -> float:
    return {
        "self": 0.0,
        "trial": 0.0,
        "pro": 100.0,
        "enterprise": 500.0,
    }.get(plan, 0.0)


def _generate_api_key(tenant_id: str) -> str:
    """Human-recognisable prefix + 32 bytes of urlsafe entropy."""
    return f"ky_{tenant_id}_{secrets.token_urlsafe(32)}"


# --------------------------------------------------------------------------- #
# Nightly / weekly run history                                                #
# --------------------------------------------------------------------------- #


def _safe_load(path: Path) -> dict[str, Any] | None:
    """Read a run-report JSON tolerantly. Returns None on any corruption."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _summarise_run(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Trim a full report down to what the UI needs for the history table."""
    stages = payload.get("stages") or []
    ok = sum(1 for s in stages if s.get("status") in ("ok", "dry_run"))
    fail = sum(1 for s in stages if s.get("status") == "fail")
    return {
        "file": path.name,
        "kind": payload.get("kind", "nightly"),
        "started_at": payload.get("started_at"),
        "ended_at": payload.get("ended_at"),
        "duration_s": payload.get("duration_s", 0.0),
        "total_rows_added": payload.get("total_rows_added", 0),
        "stage_count": len(stages),
        "stage_ok": ok,
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
