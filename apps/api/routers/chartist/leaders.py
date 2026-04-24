"""Chartist leaders / sectors / breakouts endpoints.

Routes:
    GET /leaders
    GET /sectors
    GET /breakouts/52w
    GET /breakouts/near_52w
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from routers.chartist._shared import envelope, scanning

router = APIRouter()


@router.get("/leaders")
def leaders(
    limit: int = Query(default=142, ge=1, le=500),
    market: str = Query(default="KOSPI,KOSDAQ"),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
) -> dict:
    mods = scanning()
    markets = [m.strip() for m in market.split(",") if m.strip()]
    panel = mods["loader"].load_panel(markets=markets)
    rows = mods["leaders"].scan_leaders(
        panel=panel,
        top_n=limit,
        min_leader_score=min_score,
    )
    return envelope({
        "as_of": panel.as_of,
        "universe_size": len(panel.universe),
        "count": len(rows),
        "rows": [r.to_dict() for r in rows],
    })


@router.get("/sectors")
def sectors(top_n: int = Query(default=40, ge=1, le=60)) -> dict:
    mods = scanning()
    panel = mods["loader"].load_panel()
    ss = mods["sectors"].sector_strength(panel=panel, top_n=top_n)
    return envelope({
        "as_of": panel.as_of,
        "count": len(ss),
        "rows": [mods["sectors"].to_dict(s) for s in ss],
    })


@router.get("/breakouts/52w")
def breakouts_52w(
    vol_x_min: float = Query(default=1.0, ge=0.3),
    limit: int = Query(default=100, ge=1, le=500),
    breakout_tolerance: float = Query(default=0.995, ge=0.95, le=1.0),
) -> dict:
    """Stocks trading at (or within ~0.5 %) of their 252-day high today."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    rows = mods["breakouts"].scan_breakouts(
        panel=panel,
        vol_x_min=vol_x_min,
        breakout_tolerance=breakout_tolerance,
        limit=limit,
    )
    return envelope({
        "as_of": panel.as_of,
        "count": len(rows),
        "rows": [mods["breakouts"].to_dict(r) for r in rows],
    })


@router.get("/breakouts/near_52w")
def breakouts_near_52w(
    proximity_pct: float = Query(default=2.0, ge=0.5, le=10.0),
    vol_x_min: float = Query(default=0.7, ge=0.3),
    limit: int = Query(default=150, ge=1, le=500),
) -> dict:
    """Stocks within ``proximity_pct`` of their 252-day high — breakout watchlist."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    rows = mods["breakouts"].scan_near_52w(
        panel=panel,
        proximity_pct=proximity_pct,
        vol_x_min=vol_x_min,
        limit=limit,
    )
    return envelope({
        "as_of": panel.as_of,
        "count": len(rows),
        "rows": [mods["breakouts"].to_dict(r) for r in rows],
    })
