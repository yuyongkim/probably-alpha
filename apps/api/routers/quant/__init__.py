"""Quant router — factors / backtests / macro series."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Query

router = APIRouter()
log = logging.getLogger(__name__)


@router.get("/factors")
def factors_overview() -> dict:
    return {
        "ok": True,
        "data": {"factors": [], "_placeholder": "Coming in Phase 3"},
        "error": None,
    }


@router.get("/macro/series")
def macro_series(
    source: str = Query(..., description="fred | ecos | eia | exim | ..."),
    series_id: str = Query(..., description="source-specific series id"),
    start: str | None = Query(None, description="ISO YYYY-MM-DD (optional)"),
    end: str | None = Query(None, description="ISO YYYY-MM-DD (optional)"),
    limit: int | None = Query(None, ge=1, le=10000),
    owner_id: str = Query("self"),
) -> dict:
    """Return stored macro observations for (source, series_id).

    Reads from the ky-platform SQLite store. If the store is empty or the
    ky-core package is not yet installed, returns an empty array with a
    ``stale_data`` warning rather than erroring out.
    """
    try:
        from ky_core.storage import Repository
    except Exception as exc:  # noqa: BLE001
        log.warning("ky_core.storage not importable: %s", exc)
        return {
            "ok": True,
            "data": {
                "source": source,
                "series_id": series_id,
                "observations": [],
                "stale_data": True,
                "warning": f"storage unavailable: {exc}",
            },
            "error": None,
        }

    try:
        repo = Repository(owner_id=owner_id)
        rows = repo.get_observations(source, series_id, start=start, end=end, limit=limit)
    except Exception as exc:  # noqa: BLE001
        log.exception("macro series read failed")
        return {
            "ok": False,
            "data": None,
            "error": {"code": "STORAGE_READ_FAILED", "message": str(exc), "detail": {}},
        }

    warning = None
    if not rows:
        warning = (
            "No observations in SQLite yet. Run: "
            "python scripts/collect.py --source all-macro"
        )

    return {
        "ok": True,
        "data": {
            "source": source,
            "series_id": series_id,
            "observations": rows,
            "stale_data": bool(warning),
            "warning": warning,
        },
        "error": None,
    }
