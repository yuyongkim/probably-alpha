"""Chartist wizard-screener endpoints.

Routes:
    GET /wizards           — overview (pass counts for all 6 screens)
    GET /wizards/{name}    — detail rows for a single screen
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from routers.chartist._shared import envelope, scanning

router = APIRouter()


@router.get("/wizards")
def wizards_overview() -> dict:
    """Return pass counts for all 6 wizard screens + universe size."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    out: list[dict[str, Any]] = []
    for key, cfg in mods["wizards"].REGISTRY.items():
        hits = cfg["screen"](panel)
        out.append({
            "key": key,
            "name": cfg["name"],
            "condition": cfg["condition"],
            "pass_count": len(hits),
            "total": len(panel.universe),
            "delta_vs_yesterday": 0,  # TODO: persist yesterday's counts
        })
    return envelope({
        "as_of": panel.as_of,
        "universe_size": len(panel.universe),
        "presets": out,
    })


@router.get("/wizards/{name}")
def wizard_detail(
    name: str,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    mods = scanning()
    reg = mods["wizards"].REGISTRY
    if name not in reg:
        raise HTTPException(status_code=404, detail=f"unknown wizard: {name}")
    panel = mods["loader"].load_panel()
    cfg = reg[name]
    hits = cfg["screen"](panel)[:limit]
    return envelope({
        "as_of": panel.as_of,
        "key": name,
        "name": cfg["name"],
        "condition": cfg["condition"],
        "count": len(hits),
        "rows": [h.to_dict() for h in hits],
    })
