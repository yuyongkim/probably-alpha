"""Value router — DCF / PIT 재무 / 버핏 RAG."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/dcf")
def dcf_placeholder() -> dict:
    return {
        "ok": True,
        "data": {"model": None, "_placeholder": "Coming in Phase 3 (port from Finance_analysis)"},
        "error": None,
    }
