"""Chartist router — 오늘의 시장 / 섹터 로테이션 / 리더 스캔.

Phase 3: wired to ky.db real data via ``ky_core.scanning``. The legacy
mock bundle is still available via ``?mock=true`` for backwards
compatibility with the existing UI pages while the new sub-section
pages are rolled in.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

# Make packages/core importable without requiring `pip install -e .`
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

from ky_core.chartist import get_today_bundle  # noqa: E402

from config import settings  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter()


def _envelope(data: Any = None, error: Any = None, ok: bool | None = None) -> dict:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}


# --------------------------------------------------------------------------- #
# Lazy scanning import (so the API boots even when ky.db is missing)          #
# --------------------------------------------------------------------------- #

def _scanning():
    # Import submodules directly to avoid the parent package ``__init__``
    # re-exporting helpers with the same names as the submodules (e.g.
    # ``sector_strength`` function collides with the submodule).
    import importlib
    return {
        "loader":    importlib.import_module("ky_core.scanning.loader"),
        "leaders":   importlib.import_module("ky_core.scanning.leader_scan"),
        "sectors":   importlib.import_module("ky_core.scanning.sector_strength"),
        "breakouts": importlib.import_module("ky_core.scanning.breakouts"),
        "breadth":   importlib.import_module("ky_core.scanning.breadth"),
        "wizards":   importlib.import_module("ky_core.scanning.wizards"),
    }


# --------------------------------------------------------------------------- #
# /today — real bundle (mock fallback via ?mock=true)                         #
# --------------------------------------------------------------------------- #


@router.get("/today")
def today_summary(mock: bool = Query(default=False)) -> dict:
    """Return the Chartist > 오늘의 주도주 bundle.

    Real mode (default): assembled from ky.db via ``ky_core.scanning``.
    Mock mode (``?mock=true``): returns the legacy fixture shipped in
    ``ky_core.chartist`` — kept for parity while new pages roll out.
    """
    if mock:
        bundle = get_today_bundle(owner_id=settings.platform_owner_id)
        return _envelope(bundle.model_dump())

    try:
        data = _build_today_bundle()
    except Exception as exc:  # fallback → mock so the page never 500s
        logger.exception("today_summary real build failed, falling back to mock")
        bundle = get_today_bundle(owner_id=settings.platform_owner_id)
        bundle_dict = bundle.model_dump()
        bundle_dict["_stale"] = True
        bundle_dict["_error"] = f"{type(exc).__name__}: {exc}"
        return _envelope(bundle_dict)
    return _envelope(data)


# --------------------------------------------------------------------------- #
# New endpoints (real-only)                                                   #
# --------------------------------------------------------------------------- #


@router.get("/leaders")
def leaders(
    limit: int = Query(default=142, ge=1, le=500),
    market: str = Query(default="KOSPI,KOSDAQ"),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
) -> dict:
    mods = _scanning()
    markets = [m.strip() for m in market.split(",") if m.strip()]
    panel = mods["loader"].load_panel(markets=markets)
    rows = mods["leaders"].scan_leaders(
        panel=panel,
        top_n=limit,
        min_leader_score=min_score,
    )
    return _envelope({
        "as_of": panel.as_of,
        "universe_size": len(panel.universe),
        "count": len(rows),
        "rows": [r.to_dict() for r in rows],
    })


@router.get("/sectors")
def sectors(top_n: int = Query(default=40, ge=1, le=60)) -> dict:
    mods = _scanning()
    panel = mods["loader"].load_panel()
    ss = mods["sectors"].sector_strength(panel=panel, top_n=top_n)
    return _envelope({
        "as_of": panel.as_of,
        "count": len(ss),
        "rows": [mods["sectors"].to_dict(s) for s in ss],
    })


@router.get("/breakouts/52w")
def breakouts_52w(
    vol_x_min: float = Query(default=1.5, ge=0.5),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    mods = _scanning()
    panel = mods["loader"].load_panel()
    rows = mods["breakouts"].scan_breakouts(
        panel=panel, vol_x_min=vol_x_min, limit=limit
    )
    return _envelope({
        "as_of": panel.as_of,
        "count": len(rows),
        "rows": [mods["breakouts"].to_dict(r) for r in rows],
    })


@router.get("/breadth")
def breadth() -> dict:
    mods = _scanning()
    panel = mods["loader"].load_panel()
    snap = mods["breadth"].compute_breadth(panel=panel)
    return _envelope(mods["breadth"].to_dict(snap))


@router.get("/wizards")
def wizards_overview() -> dict:
    """Return pass counts for all 6 wizard screens + universe size."""
    mods = _scanning()
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
    return _envelope({
        "as_of": panel.as_of,
        "universe_size": len(panel.universe),
        "presets": out,
    })


@router.get("/wizards/{name}")
def wizard_detail(
    name: str,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    mods = _scanning()
    reg = mods["wizards"].REGISTRY
    if name not in reg:
        raise HTTPException(status_code=404, detail=f"unknown wizard: {name}")
    panel = mods["loader"].load_panel()
    cfg = reg[name]
    hits = cfg["screen"](panel)[:limit]
    return _envelope({
        "as_of": panel.as_of,
        "key": name,
        "name": cfg["name"],
        "condition": cfg["condition"],
        "count": len(hits),
        "rows": [h.to_dict() for h in hits],
    })


# --------------------------------------------------------------------------- #
# Internals — compose real /today bundle in the legacy shape                  #
# --------------------------------------------------------------------------- #


# Color buckets mirror the mockup palette (hm-cell h0..h6).
#   <= -3%    → 1
#   -3..-1    → 2
#   -1..0     → 3
#    0..+1    → 4
#   +1..+3    → 5
#   > +3      → 6
def _heat_bucket(pct: float) -> int:
    if pct <= -3:
        return 1
    if pct <= -1:
        return 2
    if pct < 0:
        return 3
    if pct < 1:
        return 4
    if pct < 3:
        return 5
    return 6


def _build_today_bundle() -> dict:
    mods = _scanning()
    panel = mods["loader"].load_panel()

    # Full universe leader scan once → slice locally for top 10 + summary counts.
    full_leaders = mods["leaders"].scan_leaders(
        panel=panel, top_n=len(panel.universe), min_leader_score=0.0
    )
    leaders_rows = full_leaders[:10]
    secs = mods["sectors"].sector_strength(panel=panel)
    top_secs = secs[:5]
    brks = mods["breakouts"].scan_breakouts(panel=panel, limit=10)
    brd = mods["breadth"].compute_breadth(panel=panel)
    wiz_overview = []
    for key, cfg in mods["wizards"].REGISTRY.items():
        hits = cfg["screen"](panel)
        wiz_overview.append({
            "name": cfg["name"],
            "condition": cfg["condition"],
            "pass_count": len(hits),
            "total": len(panel.universe),
            "delta_vs_yesterday": 0,
        })

    # Stage distribution (from leader_scan VCP stages)
    stage_counts = [0, 0, 0, 0, 0]   # 0..4
    for l in leaders_rows:
        stage_counts[min(l.vcp_stage, 4)] += 1
    stage_palette = ["#D8E2DC", "#B4CBB8", "#7FA88A", "#2D6A4F", "#B08968"]
    stage_labels = [
        "Stage 1 (초기)",
        "Stage 2 (수축)",
        "Stage 3 (돌파 전)",
        "Breakout",
        "Extended",
    ]
    total_stage = max(1, sum(stage_counts))
    stage_dist = [
        {
            "name": stage_labels[i],
            "count": stage_counts[i],
            "pct": stage_counts[i] / total_stage * 100,
            "color_hint": stage_palette[i],
        }
        for i in range(5)
    ]

    heatmap = []
    for s in secs[:20]:
        heatmap.append({
            "name": s.name,
            "p1d": round(s.d1 * 100, 2),  "p1d_h": _heat_bucket(s.d1 * 100),
            "p1w": round(s.d5 * 100, 2),  "p1w_h": _heat_bucket(s.d5 * 100),
            "p1m": round(s.m1 * 100, 2),  "p1m_h": _heat_bucket(s.m1 * 100),
            "p3m": round(s.m3 * 100, 2),  "p3m_h": _heat_bucket(s.m3 * 100),
            "pytd": round(s.ytd * 100, 2),"pytd_h": _heat_bucket(s.ytd * 100),
        })

    top_leader = leaders_rows[0] if leaders_rows else None
    top_sector = top_secs[0] if top_secs else None
    sepa_total_rows = full_leaders
    sepa_pass_total = sum(1 for l in sepa_total_rows if l.tt_passes >= 5)

    summary = [
        {
            "label": "Top Sector",
            "value": top_sector.name if top_sector else "—",
            "delta": (
                f"{top_sector.d1*100:+.2f}% · RS {top_sector.score:.2f}"
                if top_sector else "—"
            ),
            "tone": "pos" if top_sector and top_sector.d1 >= 0 else "neg",
        },
        {
            "label": "Top Leader",
            "value": top_leader.name if top_leader else "—",
            "delta": (
                f"{top_leader.trend_template} · LS {top_leader.leader_score:.2f}"
                if top_leader else "—"
            ),
            "tone": "pos" if top_leader else "neutral",
        },
        {
            "label": "52w High",
            "value": f"{brd.new_highs_52w}",
            "delta": f"new high · new low {brd.new_lows_52w}",
            "tone": "pos" if brd.new_highs_52w >= brd.new_lows_52w else "neg",
        },
        {
            "label": "VCP Stage 3",
            "value": str(sum(1 for l in sepa_total_rows if l.vcp_stage >= 3)),
            "delta": "돌파 임박",
            "tone": "pos",
        },
        {
            "label": "SEPA Pass",
            "value": f"{sepa_pass_total} / {len(panel.universe)}",
            "delta": f"{sepa_pass_total / max(1, len(panel.universe)) * 100:.2f}% pass",
            "tone": "pos",
        },
        {
            "label": "Breadth",
            "value": f"{brd.pct_above_sma50:.1f}%",
            "delta": f">SMA50 · McC {brd.mcclellan:+.0f}",
            "tone": "pos" if brd.mcclellan >= 0 else "neg",
        },
    ]

    # Leaders in legacy Leader shape
    legacy_leaders = [
        {
            "symbol": l.symbol,
            "name": l.name,
            "sector": l.sector,
            "leader_score": round(l.leader_score, 3),
            "trend_template": l.trend_template,
            "rs": round(l.rs, 3),
            "d1": round(l.d1, 2),
            "d5": round(l.d5, 2),
            "m1": round(l.m1, 2),
            "vol_x": round(l.vol_x, 2),
            "pattern": l.pattern,
        }
        for l in leaders_rows
    ]

    legacy_sectors = [
        {
            "rank": s.rank,
            "name": s.name,
            "score": round(s.score, 3),
            "d1": round(s.d1 * 100, 2),
            "d5": round(s.d5 * 100, 2),
            "sparkline": [round(v, 3) for v in (s.sparkline[-7:] or [])],
        }
        for s in top_secs
    ]

    legacy_breakouts = [
        {
            "ticker": b.name,
            "symbol": b.symbol,
            "market": b.market,
            "pct_up": round(b.pct_up, 2),
            "vol_x": round(b.vol_x, 2),
            "sector": b.sector,
        }
        for b in brks
    ]

    return {
        "date": panel.as_of,
        "owner_id": settings.platform_owner_id,
        "universe_size": len(panel.universe),
        "market": _market_strip(brd),
        "summary": summary,
        "leaders": legacy_leaders,
        "sectors": legacy_sectors,
        "heatmap": heatmap,
        "breakouts": legacy_breakouts,
        "wizards_pass": wiz_overview,
        "stage_dist": stage_dist,
        "activity_log": [],        # TODO: wire event log (needs separate store)
        "upcoming_events": [],     # TODO: wire earnings/macro calendar
        "last_backtest_cagr": None,
    }


def _market_strip(brd) -> list[dict[str, Any]]:
    """Compact market strip. We don't have live indices here, so we surface
    breadth/flow stats in the first cells; KIS wiring will replace these."""
    tone_mc = "pos" if brd.mcclellan >= 0 else "neg"
    tone_hi = "pos" if brd.new_highs_52w >= brd.new_lows_52w else "neg"
    total_vol = brd.up_volume + brd.down_volume
    return [
        {"label": "Universe", "value": f"{brd.universe:,}", "delta": "KOSPI+KOSDAQ", "tone": "neutral"},
        {"label": "Advancers", "value": f"{brd.advancers:,}", "delta": f"vs {brd.decliners:,} dec", "tone": "pos"},
        {"label": "New 52w H", "value": f"{brd.new_highs_52w}", "delta": f"L {brd.new_lows_52w}", "tone": tone_hi},
        {"label": ">SMA50", "value": f"{brd.pct_above_sma50:.1f}%", "delta": ">SMA200 " + f"{brd.pct_above_sma200:.1f}%", "tone": "neutral"},
        {"label": "Up-Vol", "value": f"{brd.up_vol_pct:.1f}%", "delta": f"total {total_vol/1e9:.1f}B", "tone": "pos" if brd.up_vol_pct >= 50 else "neg"},
        {"label": "McClellan", "value": f"{brd.mcclellan:+.1f}", "delta": "EMA19-EMA39", "tone": tone_mc},
        {"label": "AD diff", "value": f"{brd.advancers - brd.decliners:+,}", "delta": "today", "tone": "pos" if brd.advancers >= brd.decliners else "neg"},
        {"label": "As of", "value": brd.as_of, "delta": "EOD", "tone": "neutral"},
    ]
