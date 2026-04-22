"""Execute router — 포지션 / 주문 / 리스크 가드 (KIS 연동)."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/overview")
def execute_overview() -> dict:
    return {
        "ok": True,
        "data": {
            "account": None,
            "positions": [],
            "_placeholder": "Coming in Phase 3 (port from 한국투자증권 samples)",
        },
        "error": None,
    }
