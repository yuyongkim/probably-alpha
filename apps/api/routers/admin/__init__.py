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
    verification. Used by the /admin/keys frontend page."""
    def _probe(val: str | None) -> dict:
        if not val:
            return {"configured": False, "length": 0, "last4": None}
        v = val.strip()
        return {
            "configured": True,
            "length": len(v),
            "last4": v[-4:] if len(v) >= 4 else None,
        }

    return {
        "ok": True,
        "data": {
            "keys": {
                "KIS_APP_KEY": _probe(settings.kis_app_key),
                "KIS_APP_SECRET": _probe(settings.kis_app_secret),
                "KIWOOM_APP_KEY": _probe(settings.kiwoom_app_key),
                "KIWOOM_SECRET_KEY": _probe(settings.kiwoom_secret_key),
                "DART_API_KEY": _probe(settings.dart_api_key),
                "FRED_API_KEY": _probe(settings.fred_api_key),
                "ECOS_API_KEY": _probe(settings.ecos_api_key),
                "KOSIS_API_KEY": _probe(getattr(settings, "kosis_api_key", None)),
                "EIA_API_KEY": _probe(getattr(settings, "eia_api_key", None)),
                "EXIM_API_KEY": _probe(getattr(settings, "exim_api_key", None)),
                "ANTHROPIC_API_KEY": _probe(
                    getattr(settings, "anthropic_api_key", None),
                ),
            },
            "shared_env_path": "~/.ky-platform/shared.env",
            "note": "Values are never returned. Last-4-chars shown for operator identification only.",
        },
        "error": None,
    }


@router.get("/data_health")
def admin_data_health() -> dict:
    """Aggregate health probe for every registered data adapter. Lightweight
    wrapper over each adapter's BaseAdapter.healthcheck() so the ops page
    can show a single green/red column per source."""
    import time

    results: list[dict] = []

    def _probe(name: str, factory):
        t0 = time.time()
        try:
            with factory() as a:
                hc = a.healthcheck()
            results.append({
                "source_id": getattr(a, "source_id", name),
                "name": name,
                "ok": bool(hc.get("ok")),
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "last_error": hc.get("last_error"),
                "note": hc.get("note"),
            })
        except Exception as exc:  # noqa: BLE001
            results.append({
                "source_id": name,
                "name": name,
                "ok": False,
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "last_error": f"{type(exc).__name__}: {exc}",
                "note": None,
            })

    for mod_name, cls_name in [
        ("ky_adapters.kis", "KISAdapter"),
        ("ky_adapters.dart", "DARTAdapter"),
        ("ky_adapters.fred", "FREDAdapter"),
        ("ky_adapters.ecos", "ECOSAdapter"),
        ("ky_adapters.kosis", "KOSISAdapter"),
        ("ky_adapters.eia", "EIAAdapter"),
        ("ky_adapters.exim", "EXIMAdapter"),
    ]:
        try:
            import importlib

            mod = importlib.import_module(mod_name)
            cls = getattr(mod, cls_name)
            _probe(cls_name.replace("Adapter", "").lower(), cls.from_settings)
        except Exception as exc:  # noqa: BLE001
            results.append({
                "source_id": cls_name,
                "name": cls_name,
                "ok": False,
                "latency_ms": 0,
                "last_error": f"import failed: {exc}",
                "note": None,
            })

    ok_count = sum(1 for r in results if r["ok"])
    return {
        "ok": True,
        "data": {
            "count": len(results),
            "ok_count": ok_count,
            "fail_count": len(results) - ok_count,
            "results": results,
        },
        "error": None,
    }


router.include_router(_tenants_router)
router.include_router(_usage_audit_router)
router.include_router(_runs_router)
