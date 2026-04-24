"""Usage + billing + audit-log endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Header, Query

from ky_core.storage.repository import Repository

from routers.admin._shared import is_admin, ok, plan_price

router = APIRouter()


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
    scoped = tenant_id if is_admin(x_admin_token) else "self"
    rows = repo.list_api_usage(tenant_id=scoped, since=since, limit=limit)
    summary = repo.usage_summary_by_tenant(since=since)
    if not is_admin(x_admin_token):
        summary = [s for s in summary if s["tenant_id"] == "self"]
    # Dummy pricing: self 0 / trial 0 / pro $100/mo / enterprise $500/mo
    tenant_rows = {t["tenant_id"]: t for t in repo.list_tenants()}
    for s in summary:
        plan = tenant_rows.get(s["tenant_id"], {}).get("plan", "self")
        s["plan"] = plan
        s["monthly_fee_usd"] = plan_price(plan)
    return ok(
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
    scoped = tenant_id if is_admin(x_admin_token) else "self"
    rows = repo.list_audit(tenant_id=scoped, limit=limit)
    return ok({"count": len(rows), "events": rows})
