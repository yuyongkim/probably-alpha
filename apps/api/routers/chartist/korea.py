"""Korean-market sub-sections — Flow / Themes / ShortInt / Kiwoom conditions."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from routers.chartist._shared import envelope, scanning

router = APIRouter()


@router.get("/flow")
def flow_dashboard(
    days: int = Query(default=5, ge=1, le=20),
    top_foreign: int = Query(default=15, ge=1, le=50),
    top_institution: int = Query(default=10, ge=1, le=50),
) -> dict:
    """수급 대시보드 — 외국인/기관/개인 Top N + 섹터 Heatmap."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    bundle = mods["flow"].scan_flow(
        panel=panel,
        days=days,
        top_foreign=top_foreign,
        top_institution=top_institution,
    )
    return envelope(mods["flow"].to_dict(bundle))


@router.get("/themes")
def themes_rotation(
    max_members: int = Query(default=8, ge=1, le=25),
) -> dict:
    """20 테마 순환 — equal-weighted 구성 종목 수익률."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    bundle = mods["themes"].scan_themes(panel=panel, max_members=max_members)
    return envelope(mods["themes"].to_dict(bundle))


@router.get("/themes/{code}")
def themes_detail(code: str) -> dict:
    """단일 테마 구성 종목 상세."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    bundle = mods["themes"].scan_themes(panel=panel, max_members=50)
    for row in bundle.rows:
        if row.code.lower() == code.lower() or row.name == code:
            return envelope({
                "as_of": bundle.as_of,
                "theme": {
                    **{k: v for k, v in row.__dict__.items() if k != "constituents"},
                    "constituents": [c.__dict__ for c in row.constituents],
                },
            })
    raise HTTPException(status_code=404, detail=f"unknown theme: {code}")


@router.get("/shortint")
def shortint_overview(
    top_n: int = Query(default=10, ge=1, le=50),
) -> dict:
    """공매도/대차 프록시 대시보드."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    bundle = mods["shortint"].scan_shortint(panel=panel, top_n=top_n)
    return envelope(mods["shortint"].to_dict(bundle))


@router.get("/kiwoom_cond")
def kiwoom_conditions(
    top_per_bucket: int = Query(default=30, ge=1, le=100),
    top_intersection: int = Query(default=40, ge=1, le=200),
) -> dict:
    """키움 조건식 7종 — 전 유니버스 스캔."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    bundle = mods["kiwoom"].scan_kiwoom(
        panel=panel,
        top_per_bucket=top_per_bucket,
        top_intersection=top_intersection,
    )
    return envelope(mods["kiwoom"].to_dict(bundle))
