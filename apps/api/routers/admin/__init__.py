"""Admin router — 상태 / 잡 / 감사 로그 / 시크릿 존재 여부."""
from __future__ import annotations

from fastapi import APIRouter

from config import settings

router = APIRouter()


@router.get("/status")
def admin_status() -> dict:
    """Returns service + secret-presence status. Never returns secret values."""
    return {
        "ok": True,
        "data": {
            "owner_id": settings.platform_owner_id,
            "shared_env_loaded": settings.shared_env_present,
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
