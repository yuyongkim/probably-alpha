"""ky-platform FastAPI entrypoint.

Run locally:
    uvicorn main:app --reload --port 8300
Or via the root helper:
    ./scripts/dev.sh
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from middleware.auth import TenantAuthMiddleware
from routers.admin import router as admin_router
from routers.assistant import router as assistant_router
from routers.chartist import router as chartist_router
from routers.execute import router as execute_router
from routers.quant import router as quant_router
from routers.research import router as research_router
from routers.value import router as value_router

# Make packages/core importable for the tenant bootstrap.
_PKG_CORE = Path(__file__).resolve().parents[2] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

logger = logging.getLogger(__name__)


def _bootstrap_tenants() -> None:
    """Ensure the ``self`` tenant exists — required for backwards compatibility
    with the single-user dev mode."""
    try:
        from ky_core.storage.repository import Repository

        Repository().ensure_self_tenant()
    except Exception:  # pragma: no cover — must not block API start-up
        logger.exception("tenant bootstrap failed — continuing without seed")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ky-platform API",
        version="0.1.0",
        description="probably-alpha unified financial platform backend.",
    )

    _bootstrap_tenants()

    # Order matters: Starlette wraps middlewares in LIFO order, so the last
    # ``add_middleware`` is outermost. CORS wraps TenantAuth so the browser
    # still sees CORS headers on 401/429 rejections from the auth layer.
    app.add_middleware(TenantAuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["meta"])
    def health() -> dict:
        return {
            "ok": True,
            "data": {
                "status": "ok",
                "owner_id": settings.platform_owner_id,
                "shared_env_loaded": settings.shared_env_present,
            },
            "error": None,
        }

    # Versioned mounts — all business routes under /api/v1
    app.include_router(chartist_router, prefix="/api/v1/chartist", tags=["chartist"])
    app.include_router(quant_router, prefix="/api/v1/quant", tags=["quant"])
    app.include_router(value_router, prefix="/api/v1/value", tags=["value"])
    app.include_router(execute_router, prefix="/api/v1/execute", tags=["execute"])
    app.include_router(research_router, prefix="/api/v1/research", tags=["research"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(assistant_router, prefix="/api/v1/assistant", tags=["assistant"])

    return app


app = create_app()
