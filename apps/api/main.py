"""ky-platform FastAPI entrypoint.

Run locally:
    uvicorn main:app --reload --port 8300
Or via the root helper:
    ./scripts/dev.sh
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.admin import router as admin_router
from routers.assistant import router as assistant_router
from routers.chartist import router as chartist_router
from routers.execute import router as execute_router
from routers.quant import router as quant_router
from routers.research import router as research_router
from routers.value import router as value_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="ky-platform API",
        version="0.1.0",
        description="probably-alpha unified financial platform backend.",
    )

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
