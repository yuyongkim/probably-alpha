"""Technicals sub-sections — patterns / candlestick / divergence / ichimoku /
vprofile / support. 1-hour TTL cache keyed on (endpoint, as_of).
"""
from __future__ import annotations

import time as _time

from fastapi import APIRouter, Query

from routers.chartist._shared import envelope, scanning

router = APIRouter()

_TECHNICALS_TTL = 3600.0  # 1 hour
_technicals_cache: dict[tuple, tuple[float, dict]] = {}


def _technicals_cached(key: tuple, builder):
    now = _time.time()
    hit = _technicals_cache.get(key)
    if hit and (now - hit[0]) < _TECHNICALS_TTL:
        return hit[1]
    built = builder()
    _technicals_cache[key] = (now, built)
    return built


@router.get("/patterns")
def chartist_patterns(
    limit: int = Query(default=300, ge=10, le=1000),
    pattern: str | None = Query(default=None, description="VCP | Cup&Handle | Flat Base | Asc Triangle"),
) -> dict:
    """VCP / Cup & Handle / Flat Base / Asc Triangle 베이스 패턴 스캔."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    key = ("patterns", panel.as_of, limit, pattern or "")

    def build():
        rows = mods["vcp"].scan_base_patterns(panel=panel, limit=limit)
        if pattern:
            rows = [r for r in rows if r.pattern == pattern]
        return {
            "as_of": panel.as_of,
            "universe_size": len(panel.universe),
            "count": len(rows),
            "summary": mods["vcp"].summary_counts(rows),
            "rows": [r.to_dict() for r in rows],
        }

    return envelope(_technicals_cached(key, build))


@router.get("/candlestick")
def chartist_candlestick(
    limit: int = Query(default=300, ge=10, le=1000),
    patterns: str | None = Query(default=None, description="comma-separated pattern keys"),
) -> dict:
    """캔들스틱 패턴 스캐너 — 15+ 고전 패턴 + 과거 승률/평균 5D 수익."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    pats = [p.strip() for p in patterns.split(",")] if patterns else None
    key = ("candlestick", panel.as_of, limit, patterns or "")

    def build():
        rows = mods["candlestick"].scan_candlesticks(
            panel=panel, limit=limit, patterns=pats
        )
        return {
            "as_of": panel.as_of,
            "universe_size": len(panel.universe),
            "count": len(rows),
            "summary": mods["candlestick"].summary_counts(rows),
            "rows": [r.to_dict() for r in rows],
        }

    return envelope(_technicals_cached(key, build))


@router.get("/divergence")
def chartist_divergence(
    limit: int = Query(default=300, ge=10, le=1000),
    kind: str | None = Query(
        default=None,
        description="bullish | bearish | hidden_bullish | hidden_bearish",
    ),
) -> dict:
    """RSI / MACD / OBV divergence — regular + hidden."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    key = ("divergence", panel.as_of, limit, kind or "")

    def build():
        rows = mods["divergence"].scan_divergences(panel=panel, limit=limit)
        if kind:
            rows = [r for r in rows if r.kind == kind]
        return {
            "as_of": panel.as_of,
            "universe_size": len(panel.universe),
            "count": len(rows),
            "summary": mods["divergence"].summary_counts(rows),
            "rows": [r.to_dict() for r in rows],
        }

    return envelope(_technicals_cached(key, build))


@router.get("/ichimoku")
def chartist_ichimoku(
    limit: int = Query(default=300, ge=10, le=1000),
    three_cross: bool = Query(default=False),
    vs_cloud: str | None = Query(default=None, description="ABOVE | BELOW | INSIDE"),
) -> dict:
    """Ichimoku Cloud — vs cloud 분류 + 3-cross align."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    key = ("ichimoku", panel.as_of, limit, three_cross, vs_cloud or "")

    def build():
        rows = mods["ichimoku"].scan_ichimoku(
            panel=panel, limit=limit, require_three_cross=three_cross
        )
        if vs_cloud:
            rows = [r for r in rows if r.vs_cloud == vs_cloud.upper()]
        return {
            "as_of": panel.as_of,
            "universe_size": len(panel.universe),
            "count": len(rows),
            "summary": mods["ichimoku"].summary_counts(rows),
            "rows": [r.to_dict() for r in rows],
        }

    return envelope(_technicals_cached(key, build))


@router.get("/vprofile")
def chartist_vprofile(
    limit: int = Query(default=300, ge=10, le=1000),
    lookback: int = Query(default=60, ge=20, le=252),
    position: str | None = Query(
        default=None,
        description="ABOVE_VAH | NEAR_POC | INSIDE_VA | BELOW_VAL",
    ),
) -> dict:
    """Volume Profile (VPVR) — POC / VAH / VAL 위치 분류."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    key = ("vprofile", panel.as_of, limit, lookback, position or "")

    def build():
        rows = mods["vprofile"].scan_vprofile(
            panel=panel, limit=limit, lookback=lookback
        )
        if position:
            rows = [r for r in rows if r.position == position.upper()]
        return {
            "as_of": panel.as_of,
            "universe_size": len(panel.universe),
            "count": len(rows),
            "summary": mods["vprofile"].summary_counts(rows),
            "rows": [r.to_dict() for r in rows],
        }

    return envelope(_technicals_cached(key, build))


@router.get("/support")
def chartist_support(
    limit: int = Query(default=300, ge=10, le=1000),
    state: str | None = Query(default=None, description="AT_S | AT_R | MID"),
) -> dict:
    """지지/저항 자동감지 — 피벗 포인트 + 장기 고점/저점 (5% 중복 제거)."""
    mods = scanning()
    panel = mods["loader"].load_panel()
    key = ("support", panel.as_of, limit, state or "")

    def build():
        rows = mods["support"].scan_support_resistance(panel=panel, limit=limit)
        if state:
            rows = [r for r in rows if r.state == state.upper()]
        return {
            "as_of": panel.as_of,
            "universe_size": len(panel.universe),
            "count": len(rows),
            "summary": mods["support"].summary_counts(rows),
            "rows": [r.to_dict() for r in rows],
        }

    return envelope(_technicals_cached(key, build))
