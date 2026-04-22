"""Quant router — 팩터 / 백테스트 / 리서치 노트북."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/factors")
def factors_overview() -> dict:
    return {
        "ok": True,
        "data": {"factors": [], "_placeholder": "Coming in Phase 3"},
        "error": None,
    }
