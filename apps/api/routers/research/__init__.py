"""Research router — 논문 / 리포트 / 매크로."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/papers")
def papers_index() -> dict:
    return {
        "ok": True,
        "data": {"papers": [], "_placeholder": "Coming in Phase 3 (port from Dart_Analysis)"},
        "error": None,
    }
