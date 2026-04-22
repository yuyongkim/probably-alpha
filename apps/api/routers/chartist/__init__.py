"""Chartist router — 오늘의 시장 / 섹터 로테이션 / 리더 스캔."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/today")
def today_summary() -> dict:
    """Placeholder — returns the shape the frontend expects.

    Phase 3 will wire this to services/chartist_today.py
    (섹터 스코어 + 리더 TopN + 마지막 BT 요약).
    """
    return {
        "ok": True,
        "data": {
            "date": None,
            "top_sectors": [],
            "top_leaders": [],
            "last_backtest": None,
            "_placeholder": "Coming in Phase 3",
        },
        "error": None,
    }
