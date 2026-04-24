"""Shared helpers for admin sub-routers — envelope, admin-token guard,
tenant sanitisation, plan defaults, API-key generation.
"""
from __future__ import annotations

import secrets
import sys
from pathlib import Path
from typing import Any

from fastapi import HTTPException

# Make packages/core importable (mirrors routers/chartist bootstrap).
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

from config import settings  # noqa: E402

# Reports land here via scripts/nightly.py and scripts/weekly.py.
# Mirrored as a constant so the frontend can show the origin path.
OPS_DIR = Path.home() / ".ky-platform" / "data" / "ops"


def ok(data: Any) -> dict:
    return {"ok": True, "data": data, "error": None}


def err(code: str, message: str, *, detail: dict | None = None) -> dict:
    return {
        "ok": False,
        "data": None,
        "error": {"code": code, "message": message, "detail": detail or {}},
    }


def require_admin(header_value: str | None) -> None:
    """Gate mutating endpoints. When ``KY_ADMIN_TOKEN`` is unset ALL mutations
    are refused — we never silently open up the control plane."""
    token = settings.ky_admin_token
    if not token:
        raise HTTPException(status_code=403, detail="KY_ADMIN_TOKEN is not configured")
    if header_value != token:
        raise HTTPException(status_code=401, detail="invalid admin token")


def is_admin(header_value: str | None) -> bool:
    token = settings.ky_admin_token
    return bool(token) and header_value == token


def public_tenant(row: dict[str, Any]) -> dict[str, Any]:
    """Never return the api_key_hash over the wire."""
    return {k: v for k, v in row.items() if k != "api_key_hash"}


def plan_default_rate(plan: str) -> int:
    return {
        "self": 9999,
        "trial": 30,
        "pro": 300,
        "enterprise": 1200,
    }.get(plan, 60)


def plan_price(plan: str) -> float:
    return {
        "self": 0.0,
        "trial": 0.0,
        "pro": 100.0,
        "enterprise": 500.0,
    }.get(plan, 0.0)


def generate_api_key(tenant_id: str) -> str:
    """Human-recognisable prefix + 32 bytes of urlsafe entropy."""
    return f"ky_{tenant_id}_{secrets.token_urlsafe(32)}"
