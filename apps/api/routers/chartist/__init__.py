"""Chartist router — 오늘의 시장 / 섹터 로테이션 / 리더 스캔.

Phase 3: wired to ky.db real data via ``ky_core.scanning``. The legacy
mock bundle is still available via ``?mock=true`` for backwards
compatibility with the existing UI pages while the new sub-section
pages are rolled in.

Structure:
    _shared.py   — envelope + lazy scanning-module loader
    leaders.py   — /leaders, /sectors, /breakouts/*
    wizards.py   — /wizards, /wizards/{name}
    technicals.py— /patterns, /candlestick, /divergence, /ichimoku,
                   /vprofile, /support (1-hour cache)
    korea.py     — /flow, /themes, /themes/{code}, /shortint, /kiwoom_cond
    backtest.py  — /backtest/* (list / read / run)

This __init__ retains the multi-section /today bundle and bare
diagnostics (/as_of, /breadth, /ohlcv/{symbol}).
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any

from fastapi import APIRouter, Query

from config import settings
from routers.chartist._shared import envelope as _envelope, scanning as _scanning
from routers.chartist.backtest import router as backtest_router
from routers.chartist.korea import router as korea_router
from routers.chartist.leaders import router as leaders_router
from routers.chartist.technicals import router as technicals_router
from routers.chartist.wizards import router as wizards_router

# Import the legacy mock bundle builder (triggers ky_core path shim via _shared).
from ky_core.chartist import get_today_bundle  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter()

# /today bundle cache — compute is ~20s cold. Data only flips after nightly,
# so a 10-minute TTL is a huge win without risking staleness users would notice.
# Keyed by owner_id so multi-tenant bundles don't collide.
_TODAY_TTL_SEC = 600
_today_cache: dict[str, tuple[float, dict]] = {}
_today_lock = threading.Lock()

# Real-data sub-routers — paths unchanged.
router.include_router(backtest_router, prefix="/backtest")
router.include_router(leaders_router)      # /leaders, /sectors, /breakouts/*
router.include_router(wizards_router)      # /wizards, /wizards/{name}
router.include_router(technicals_router)   # /patterns, /candlestick, /divergence, /ichimoku, /vprofile, /support
router.include_router(korea_router)        # /flow, /themes, /themes/{code}, /shortint, /kiwoom_cond


# --------------------------------------------------------------------------- #
# /today — real bundle (mock fallback via ?mock=true)                         #
# --------------------------------------------------------------------------- #


@router.get("/today")
def today_summary(
    mock: bool = Query(default=False),
    no_cache: bool = Query(default=False, description="bypass the 10-min TTL cache"),
) -> dict:
    """Return the Chartist > 오늘의 주도주 bundle.

    Real mode (default): assembled from ky.db via ``ky_core.scanning``.
    Mock mode (``?mock=true``): returns the legacy fixture shipped in
    ``ky_core.chartist`` — kept for parity while new pages roll out.

    The real build is ~20s cold. We cache the result for 10 minutes keyed by
    owner_id; ``?no_cache=true`` forces a rebuild. On compute failure we
    serve the previously-cached bundle when available (flagged ``_stale``),
    otherwise fall back to the mock fixture.
    """
    if mock:
        bundle = get_today_bundle(owner_id=settings.platform_owner_id)
        return _envelope(bundle.model_dump())

    owner = settings.platform_owner_id
    now = time.time()

    # Fast path: cache hit.
    if not no_cache:
        cached = _today_cache.get(owner)
        if cached and (now - cached[0]) < _TODAY_TTL_SEC:
            data = dict(cached[1])
            data["_cached_at"] = int(cached[0])
            data["_cache_age_s"] = int(now - cached[0])
            return _envelope(data)

    # Slow path: rebuild (single-flight guard so we don't pay the 20s N times
    # when a burst of requests arrives on a cold cache).
    with _today_lock:
        # Re-check after acquiring the lock — another thread may have filled it.
        if not no_cache:
            cached = _today_cache.get(owner)
            if cached and (now - cached[0]) < _TODAY_TTL_SEC:
                data = dict(cached[1])
                data["_cached_at"] = int(cached[0])
                data["_cache_age_s"] = int(now - cached[0])
                return _envelope(data)

        try:
            data = _build_today_bundle()
            _today_cache[owner] = (time.time(), data)
            return _envelope(data)
        except Exception as exc:
            logger.exception("today_summary real build failed")
            # Prefer a stale cached value if we have one — better than the mock.
            cached = _today_cache.get(owner)
            if cached:
                data = dict(cached[1])
                data["_stale"] = True
                data["_error"] = f"{type(exc).__name__}: {exc}"
                data["_cache_age_s"] = int(now - cached[0])
                return _envelope(data)
            # No cache yet — fall back to the mock fixture.
            bundle = get_today_bundle(owner_id=owner)
            bundle_dict = bundle.model_dump()
            bundle_dict["_stale"] = True
            bundle_dict["_error"] = f"{type(exc).__name__}: {exc}"
            return _envelope(bundle_dict)


# --------------------------------------------------------------------------- #
# Bare diagnostics                                                            #
# --------------------------------------------------------------------------- #


@router.get("/ohlcv/{symbol}")
def ohlcv_series(
    symbol: str,
    days: int = Query(default=250, ge=10, le=1000),
) -> dict:
    """Daily OHLCV + SMA50 + SMA200 for a single symbol.

    Backs the StockDetailModal ChartPane (and any other real-chart surface).
    SMAs are computed server-side so the client renderer stays trivial.
    """
    from sqlalchemy import text
    from ky_core.storage.db import get_engine, init_db

    init_db()
    engine = get_engine()
    # Pull `days + 200` so SMA200 has enough history before the visible window.
    lookback_rows = days + 220
    with engine.connect() as conn:
        rs = conn.execute(
            text(
                """
                SELECT date, open, high, low, close, volume, market
                FROM ohlcv
                WHERE symbol = :sym
                  AND owner_id = 'self'
                ORDER BY date DESC
                LIMIT :lim
                """
            ),
            {"sym": symbol, "lim": lookback_rows},
        )
        rows = [
            {
                "date": r.date,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "volume": r.volume,
                "market": r.market,
            }
            for r in rs
        ]
    if not rows:
        return _envelope(
            None,
            error={"code": "NO_DATA", "message": f"no ohlcv for {symbol}"},
            ok=False,
        )

    rows.reverse()  # ascending by date

    closes = [r["close"] for r in rows]
    sma50 = _sma(closes, 50)
    sma200 = _sma(closes, 200)

    # Only expose the latest `days` rows but preserve the SMA alignment.
    visible = rows[-days:]
    sma50_v = sma50[-days:]
    sma200_v = sma200[-days:]

    candles = []
    for i, r in enumerate(visible):
        candles.append(
            {
                "date": r["date"],
                "open": r["open"],
                "high": r["high"],
                "low": r["low"],
                "close": r["close"],
                "volume": r["volume"],
                "sma50": sma50_v[i],
                "sma200": sma200_v[i],
            }
        )

    return _envelope(
        {
            "symbol": symbol,
            "market": visible[-1]["market"] if visible else None,
            "as_of": visible[-1]["date"] if visible else None,
            "count": len(candles),
            "candles": candles,
        }
    )


def _sma(values: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    running = 0.0
    for i, v in enumerate(values):
        running += v or 0
        if i >= window:
            running -= values[i - window] or 0
        if i >= window - 1:
            out.append(round(running / window, 4))
        else:
            out.append(None)
    return out


@router.get("/as_of")
def as_of_latest() -> dict:
    """Latest 'full coverage' trading day in ky.db.

    Used by the web UI to render an "as-of" badge on every page so users can
    see at a glance whether the data is actually today's close or stale."""
    mods = _scanning()
    panel = mods["loader"].load_panel()
    from datetime import date as _date
    today = _date.today().isoformat()
    return _envelope(
        {
            "as_of": panel.as_of,
            "today": today,
            "stale": panel.as_of < today,
            "universe_size": len(panel.universe),
        }
    )


@router.get("/breadth")
def breadth() -> dict:
    mods = _scanning()
    panel = mods["loader"].load_panel()
    snap = mods["breadth"].compute_breadth(panel=panel)
    return _envelope(mods["breadth"].to_dict(snap))


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
