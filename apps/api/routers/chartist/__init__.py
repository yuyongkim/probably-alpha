"""Chartist router — 오늘의 시장 / 섹터 로테이션 / 리더 스캔."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter

# Make packages/core importable without requiring `pip install -e .`
# (dev.sh / dev.bat don't necessarily install local packages yet).
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

from ky_core.chartist import get_today_bundle  # noqa: E402

from config import settings  # noqa: E402

router = APIRouter()


@router.get("/today")
def today_summary() -> dict:
    """Return the bundle powering the Chartist > 오늘의 주도주 page.

    Owner-scoped (multi-tenant ready). Phase 3 will replace the mock
    bundle inside ky_core.chartist with live sector/leader scoring.
    """
    bundle = get_today_bundle(owner_id=settings.platform_owner_id)
    return {
        "ok": True,
        "data": bundle.model_dump(),
        "error": None,
    }
