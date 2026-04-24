"""Admin router — 상태 / 잡 / 감사 로그 / 시크릿 존재 여부 / 테넌트 관리.

Structure:
    _shared.py     — ok/err envelopes, admin-token guard, plan defaults, key gen
    tenants.py     — /tenants (GET/POST), /tenants/{id}/rotate, /tenants/{id} DELETE
    usage_audit.py — /usage, /audit
    runs.py        — /nightly_runs, /weekly_runs

This __init__ keeps the tiny ``/status`` probe and mounts the sub-routers.
"""
from __future__ import annotations

from fastapi import APIRouter

from config import settings
from routers.admin.runs import router as _runs_router
from routers.admin.tenants import router as _tenants_router
from routers.admin.usage_audit import router as _usage_audit_router

router = APIRouter()


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


router.include_router(_tenants_router)
router.include_router(_usage_audit_router)
router.include_router(_runs_router)
