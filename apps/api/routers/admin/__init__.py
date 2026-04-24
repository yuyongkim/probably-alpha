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


@router.get("/keys")
def admin_keys() -> dict:
    """Enumerate which external-service keys are configured. Never returns
    the values — only presence + length + last-4-chars for operator
    verification. Shape matches the frontend KeysResponse contract in
    apps/web/types/admin.ts: ``keys`` is an array of {name, status, …}."""
    def _entry(name: str, val: str | None) -> dict:
        if not val:
            return {"name": name, "status": "missing", "length": 0, "last4": None}
        v = val.strip()
        return {
            "name": name,
            "status": "present",
            "length": len(v),
            "last4": v[-4:] if len(v) >= 4 else None,
        }

    keys = [
        _entry("KIS_APP_KEY", settings.kis_app_key),
        _entry("KIS_APP_SECRET", settings.kis_app_secret),
        _entry("KIWOOM_APP_KEY", settings.kiwoom_app_key),
        _entry("KIWOOM_SECRET_KEY", settings.kiwoom_secret_key),
        _entry("DART_API_KEY", settings.dart_api_key),
        _entry("FRED_API_KEY", settings.fred_api_key),
        _entry("ECOS_API_KEY", settings.ecos_api_key),
        _entry("KOSIS_API_KEY", getattr(settings, "kosis_api_key", None)),
        _entry("EIA_API_KEY", getattr(settings, "eia_api_key", None)),
        _entry("EXIM_API_KEY", getattr(settings, "exim_api_key", None)),
        _entry("ANTHROPIC_API_KEY", getattr(settings, "anthropic_api_key", None)),
    ]

    return {
        "ok": True,
        "data": {
            "keys": keys,
            "shared_env_loaded": settings.shared_env_present,
            "shared_env_path": "~/.ky-platform/shared.env",
            "note": "Values are never returned. Last-4-chars shown for operator identification only.",
        },
        "error": None,
    }


@router.get("/data_health")
def admin_data_health() -> dict:
    """Aggregate health probe for every registered data adapter. Response
    shape matches the frontend DataHealth contract: ``adapters`` is an
    array of {source_id, ok, latency_ms, last_error, configured, import_error}.
    """
    import time

    adapters: list[dict] = []

    def _probe(name: str, factory):
        t0 = time.time()
        try:
            with factory() as a:
                hc = a.healthcheck()
            adapters.append({
                "source_id": getattr(a, "source_id", name),
                "ok": bool(hc.get("ok")),
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "last_error": hc.get("last_error"),
                "configured": True,
            })
        except Exception as exc:  # noqa: BLE001
            adapters.append({
                "source_id": name,
                "ok": False,
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "last_error": f"{type(exc).__name__}: {exc}",
                "configured": True,
            })

    for mod_name, cls_name, src_id in [
        ("ky_adapters.kis", "KISAdapter", "kis"),
        ("ky_adapters.dart", "DARTAdapter", "dart"),
        ("ky_adapters.fred", "FREDAdapter", "fred"),
        ("ky_adapters.ecos", "ECOSAdapter", "ecos"),
        ("ky_adapters.kosis", "KOSISAdapter", "kosis"),
        ("ky_adapters.eia", "EIAAdapter", "eia"),
        ("ky_adapters.exim", "EXIMAdapter", "exim"),
    ]:
        try:
            import importlib

            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name)
            _probe(src_id, cls.from_settings)
        except Exception as exc:  # noqa: BLE001
            adapters.append({
                "source_id": src_id,
                "ok": False,
                "latency_ms": 0,
                "last_error": None,
                "configured": False,
                "import_error": str(exc),
            })

    ok_count = sum(1 for r in adapters if r["ok"])
    return {
        "ok": True,
        "data": {
            "adapters": adapters,
            "count": len(adapters),
            "ok_count": ok_count,
            "fail_count": len(adapters) - ok_count,
        },
        "error": None,
    }


router.include_router(_tenants_router)
router.include_router(_usage_audit_router)
router.include_router(_runs_router)
