"""Tenant CRUD endpoints — list / create / rotate-key / disable."""
from __future__ import annotations

import json

from fastapi import APIRouter, Header

from ky_core.storage.repository import Repository

from middleware.auth import hash_api_key
from routers.admin._shared import (
    err,
    generate_api_key,
    is_admin,
    ok,
    plan_default_rate,
    public_tenant,
    require_admin,
)

router = APIRouter()


@router.get("/tenants")
def list_tenants(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    """List tenants. GET is allowed without an admin token, but a non-admin
    caller only ever sees the ``self`` row — matching the spec's default."""
    repo = Repository()
    repo.ensure_self_tenant()
    if is_admin(x_admin_token):
        rows = repo.list_tenants()
    else:
        self_row = repo.get_tenant("self")
        rows = [self_row] if self_row else []
    return ok({"count": len(rows), "tenants": [public_tenant(r) for r in rows]})


@router.post("/tenants")
def create_tenant(
    payload: dict,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    require_admin(x_admin_token)

    tenant_id = (payload.get("tenant_id") or "").strip()
    display_name = (payload.get("display_name") or tenant_id).strip()
    plan = (payload.get("plan") or "trial").strip()
    rate_limit = int(payload.get("rate_limit_per_min") or plan_default_rate(plan))
    enabled = bool(payload.get("enabled", True))
    if not tenant_id or not tenant_id.replace("_", "").replace("-", "").isalnum():
        return err("INVALID_TENANT_ID", "tenant_id must be alphanumeric (- and _ allowed)")
    if tenant_id == "self":
        return err("RESERVED", "'self' is reserved for the built-in tenant")

    repo = Repository()
    repo.ensure_self_tenant()
    if repo.get_tenant(tenant_id):
        return err("ALREADY_EXISTS", f"tenant '{tenant_id}' already exists")

    api_key = generate_api_key(tenant_id)
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
    return ok({"tenant": public_tenant(row), "api_key": api_key})


@router.post("/tenants/{tenant_id}/rotate")
def rotate_tenant_key(
    tenant_id: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    require_admin(x_admin_token)
    if tenant_id == "self":
        return err("RESERVED", "cannot rotate key for the built-in 'self' tenant")
    repo = Repository()
    api_key = generate_api_key(tenant_id)
    row = repo.rotate_tenant_api_key(tenant_id, hash_api_key(api_key))
    if row is None:
        return err("NOT_FOUND", f"tenant '{tenant_id}' not found")
    repo.log_audit(
        tenant_id="self",
        action="tenant_key_rotated",
        detail=json.dumps({"target": tenant_id}),
    )
    return ok({"tenant": public_tenant(row), "api_key": api_key})


@router.delete("/tenants/{tenant_id}")
def disable_tenant(
    tenant_id: str,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> dict:
    require_admin(x_admin_token)
    if tenant_id == "self":
        return err("RESERVED", "cannot disable the built-in 'self' tenant")
    repo = Repository()
    row = repo.set_tenant_enabled(tenant_id, False)
    if row is None:
        return err("NOT_FOUND", f"tenant '{tenant_id}' not found")
    repo.log_audit(
        tenant_id="self",
        action="tenant_disabled",
        detail=json.dumps({"target": tenant_id}),
    )
    return ok({"tenant": public_tenant(row)})
