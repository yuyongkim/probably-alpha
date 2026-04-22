"""Quant router — factors / academic / smart-beta / PIT / IC / macro."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

# Make packages/core importable without requiring `pip install -e .`
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

router = APIRouter()
log = logging.getLogger(__name__)

_DEFAULT_AS_OF = "2026-04-17"


def _envelope(data: Any = None, error: Any = None, ok: Optional[bool] = None) -> Dict[str, Any]:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}


def _markets(markets: str) -> tuple[str, ...]:
    allowed = {"KOSPI", "KOSDAQ", "KONEX"}
    picks = tuple(m.strip().upper() for m in markets.split(",") if m.strip())
    picks = tuple(m for m in picks if m in allowed)
    return picks or ("KOSPI", "KOSDAQ")


# --------------------------------------------------------------------------- #
# Factor screener                                                             #
# --------------------------------------------------------------------------- #


@router.get("/factors")
def factors(
    as_of: str = Query(_DEFAULT_AS_OF, description="YYYY-MM-DD"),
    market: str = Query("KOSPI,KOSDAQ"),
    sort: str = Query("composite", description="composite|momentum|value|quality|low_vol|growth"),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """Universe-wide factor scan with percentile ranks."""
    try:
        from ky_core.quant import factors as ky_factors
        rows = ky_factors.scan(as_of, _markets(market))
    except Exception as exc:  # noqa: BLE001
        log.exception("factor scan failed")
        return _envelope(None, error={"code": "FACTOR_SCAN_FAILED", "message": str(exc)}, ok=False)
    if sort != "composite":
        rows = [r for r in rows if r.get(sort) is not None]
        rows.sort(key=lambda r: r[sort], reverse=True)
    rows = rows[:limit]
    return _envelope({"as_of": as_of, "sort": sort, "n": len(rows), "rows": rows})


# --------------------------------------------------------------------------- #
# Academic strategies                                                         #
# --------------------------------------------------------------------------- #


@router.get("/academic/{strategy}")
def academic_endpoint(
    strategy: str,
    as_of: str = Query(_DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.quant import academic as ky_academic
        if strategy == "magic_formula":
            rows = ky_academic.magic_formula(as_of, n=n)
        elif strategy == "deep_value":
            rows = ky_academic.deep_value(as_of, n=n)
        elif strategy == "fast_growth":
            rows = ky_academic.fast_growth(as_of, n=n)
        elif strategy == "super_quant":
            rows = ky_academic.super_quant(as_of, n=n)
        else:
            return _envelope(None, error={
                "code": "UNKNOWN_STRATEGY",
                "message": f"{strategy} not in magic_formula|deep_value|fast_growth|super_quant",
            }, ok=False)
    except Exception as exc:  # noqa: BLE001
        log.exception("academic strategy failed")
        return _envelope(None, error={"code": "ACADEMIC_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"as_of": as_of, "strategy": strategy, "n": len(rows), "rows": rows})


# --------------------------------------------------------------------------- #
# Smart Beta                                                                  #
# --------------------------------------------------------------------------- #


@router.get("/smart_beta")
def smart_beta(
    variant: str = Query("equal_weight"),
    as_of: str = Query(_DEFAULT_AS_OF),
    n: int = Query(50, ge=1, le=200),
) -> dict:
    try:
        from ky_core.quant import smart_beta as ky_smart_beta
        bundle = ky_smart_beta.build(variant, as_of=as_of, n=n)
    except ValueError as exc:
        return _envelope(None, error={"code": "UNKNOWN_VARIANT", "message": str(exc)}, ok=False)
    except Exception as exc:  # noqa: BLE001
        log.exception("smart beta build failed")
        return _envelope(None, error={"code": "SMART_BETA_FAILED", "message": str(exc)}, ok=False)
    return _envelope(bundle)


# --------------------------------------------------------------------------- #
# PIT financials                                                              #
# --------------------------------------------------------------------------- #


@router.get("/pit/{symbol}")
def pit_endpoint(
    symbol: str,
    as_of: str = Query(_DEFAULT_AS_OF),
) -> dict:
    try:
        from ky_core.quant import pit as ky_pit
        from ky_core.storage import Repository
        repo = Repository()
        ttm = ky_pit.ttm_fin(repo, symbol, as_of=as_of)
        series = ky_pit.fin_series(repo, symbol, n=12)
        meta = ky_pit.universe_meta(repo, symbol)
    except Exception as exc:  # noqa: BLE001
        log.exception("pit endpoint failed")
        return _envelope(None, error={"code": "PIT_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"symbol": symbol, "as_of": as_of, "meta": meta, "ttm": ttm, "series": series})


# --------------------------------------------------------------------------- #
# Factor IC                                                                   #
# --------------------------------------------------------------------------- #


@router.get("/ic")
def ic_endpoint(
    factor: str = Query("momentum"),
    period: str = Query("6m"),
    as_of: str = Query("2025-04-17"),
) -> dict:
    try:
        from ky_core.quant import ic as ky_ic
        result = ky_ic.factor_ic(factor, as_of=as_of, period=period, sample=200)
    except Exception as exc:  # noqa: BLE001
        log.exception("factor IC failed")
        return _envelope(None, error={"code": "IC_FAILED", "message": str(exc)}, ok=False)
    return _envelope(result)


# --------------------------------------------------------------------------- #
# Universe                                                                    #
# --------------------------------------------------------------------------- #


@router.get("/universe")
def universe(
    market: str = Query("KOSPI,KOSDAQ"),
    limit: int = Query(500, ge=1, le=5000),
) -> dict:
    try:
        from ky_core.quant import factors as ky_factors
        from ky_core.storage import Repository
        repo = Repository()
        rows = ky_factors._load_universe(repo, _markets(market))[:limit]
    except Exception as exc:  # noqa: BLE001
        log.exception("universe load failed")
        return _envelope(None, error={"code": "UNIVERSE_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"market": _markets(market), "n": len(rows), "rows": rows})


@router.get("/macro/series")
def macro_series(
    source: str = Query(..., description="fred | ecos | eia | exim | ..."),
    series_id: str = Query(..., description="source-specific series id"),
    start: str | None = Query(None, description="ISO YYYY-MM-DD (optional)"),
    end: str | None = Query(None, description="ISO YYYY-MM-DD (optional)"),
    limit: int | None = Query(None, ge=1, le=10000),
    owner_id: str = Query("self"),
) -> dict:
    """Return stored macro observations for (source, series_id)."""
    try:
        from ky_core.storage import Repository
    except Exception as exc:  # noqa: BLE001
        log.warning("ky_core.storage not importable: %s", exc)
        return _envelope({
            "source": source,
            "series_id": series_id,
            "observations": [],
            "stale_data": True,
            "warning": f"storage unavailable: {exc}",
        })

    try:
        repo = Repository(owner_id=owner_id)
        rows = repo.get_observations(source, series_id, start=start, end=end, limit=limit)
    except Exception as exc:  # noqa: BLE001
        log.exception("macro series read failed")
        return _envelope(None, error={"code": "STORAGE_READ_FAILED", "message": str(exc)}, ok=False)

    warning = None
    if not rows:
        warning = (
            "No observations in SQLite yet. Run: "
            "python scripts/collect.py --source all-macro"
        )

    return _envelope({
        "source": source,
        "series_id": series_id,
        "observations": rows,
        "stale_data": bool(warning),
        "warning": warning,
    })


# --------------------------------------------------------------------------- #
# Macro compass / regime                                                      #
# --------------------------------------------------------------------------- #


@router.get("/macro/compass")
def macro_compass(owner_id: str = Query("self")) -> dict:
    """Return the 4-axis compass + current regime hint."""
    try:
        from ky_core.macro import compute_compass, sector_playbook
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    res = compute_compass(owner_id=owner_id)
    return _envelope({
        **res.to_dict(),
        "playbook": sector_playbook(res.regime_hint),
    })


@router.get("/macro/regime")
def macro_regime(owner_id: str = Query("self")) -> dict:
    """Return 4-state regime probabilities + 12-month history."""
    try:
        from ky_core.macro import classify_regime
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    res = classify_regime(owner_id=owner_id)
    return _envelope(res.to_dict())


# --------------------------------------------------------------------------- #
# Correlation heatmap                                                         #
# --------------------------------------------------------------------------- #


@router.get("/macro/corr")
def macro_corr(
    window: int = Query(60, ge=20, le=500),
    owner_id: str = Query("self"),
) -> dict:
    """Rough KOSPI sector-vs-macro correlation over a recent window.

    Pulls sector averages from OHLCV+Universe and correlates their returns
    against FRED DFF (Fed Funds) and GDP growth levels.
    """
    try:
        from ky_core.storage import Repository
        from ky_core.storage.db import get_engine
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)

    repo = Repository(owner_id=owner_id)
    try:
        cells = _build_corr_cells(repo, get_engine(), window=window)
    except Exception as exc:  # noqa: BLE001
        log.exception("corr build failed")
        return _envelope(None, error={"code": "COMPUTE_FAILED", "message": str(exc)}, ok=False)
    return _envelope(cells)


def _build_corr_cells(repo, engine, *, window: int) -> Dict[str, Any]:
    from sqlalchemy import text

    # 1) latest `window` trading days from ohlcv
    with engine.connect() as conn:
        date_rows = conn.execute(
            text(
                "SELECT DISTINCT date FROM ohlcv WHERE owner_id = :o "
                "ORDER BY date DESC LIMIT :w"
            ),
            {"o": "self", "w": window + 5},
        ).all()
    dates = sorted([r[0] for r in date_rows])[-window:]
    if len(dates) < 10:
        return {"sectors": [], "macros": [], "cells": [], "warning": "insufficient OHLCV"}
    start = dates[0]
    end = dates[-1]

    # 2) sector daily return
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT u.sector, o.date, AVG(o.close) as avg_close "
                "FROM ohlcv o JOIN universe u "
                "  ON o.symbol = u.ticker AND o.owner_id = u.owner_id "
                "WHERE o.owner_id = :o AND o.date >= :s AND o.date <= :e "
                "  AND u.sector IS NOT NULL AND o.close > 0 "
                "GROUP BY u.sector, o.date"
            ),
            {"o": "self", "s": start, "e": end},
        ).all()
    sector_map: Dict[str, Dict[str, float]] = {}
    for sector, d, avg_close in rows:
        if not sector:
            continue
        sector_map.setdefault(sector, {})[d] = float(avg_close)

    sector_returns: Dict[str, List[float]] = {}
    for sec, dmap in sector_map.items():
        rets: List[float] = []
        for i in range(1, len(dates)):
            p0, p1 = dmap.get(dates[i - 1]), dmap.get(dates[i])
            if p0 and p1 and p0 > 0:
                rets.append(p1 / p0 - 1.0)
        if len(rets) >= max(20, window // 3):
            sector_returns[sec] = rets

    # 3) macro series — aligned to same date axis
    macros = [("fred", "DFF"), ("fred", "GDP"), ("ecos", "722Y001/0101000")]
    macro_series: Dict[str, List[float]] = {}
    for src, sid in macros:
        obs = repo.get_observations(src, sid, start=start, end=end)
        vals = [float(o["value"]) for o in obs if o.get("value") is not None]
        if len(vals) < 4:
            continue
        diffs: List[float] = []
        for i in range(1, len(vals)):
            if vals[i - 1] != 0:
                diffs.append(vals[i] / vals[i - 1] - 1.0)
        if diffs:
            macro_series[f"{src}:{sid}"] = diffs

    # Truncate all series to shortest length so correlation is comparable.
    all_series = {**{f"sector:{k}": v for k, v in sector_returns.items()}, **macro_series}
    if not all_series:
        return {"sectors": [], "macros": [], "cells": [], "warning": "no data"}
    min_len = min(len(v) for v in all_series.values())
    for k in list(all_series.keys()):
        all_series[k] = all_series[k][-min_len:]

    def _corr(xs: List[float], ys: List[float]) -> float:
        n = len(xs)
        if n < 5:
            return 0.0
        mx = sum(xs) / n
        my = sum(ys) / n
        num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
        dx = (sum((xs[i] - mx) ** 2 for i in range(n))) ** 0.5
        dy = (sum((ys[i] - my) ** 2 for i in range(n))) ** 0.5
        if dx == 0 or dy == 0:
            return 0.0
        return num / (dx * dy)

    sector_names = sorted(sector_returns.keys())
    macro_names = sorted(macro_series.keys())
    cells: List[Dict[str, Any]] = []
    for s in sector_names:
        for m in macro_names:
            c = _corr(all_series[f"sector:{s}"], all_series[m])
            cells.append({"sector": s, "macro": m, "corr": round(c, 4)})
    return {
        "window": min_len,
        "sectors": sector_names,
        "macros": macro_names,
        "cells": cells,
    }


# --------------------------------------------------------------------------- #
# Rotation playbook                                                           #
# --------------------------------------------------------------------------- #


@router.get("/macro/rotation")
def macro_rotation(owner_id: str = Query("self")) -> dict:
    """Current regime → recommended sectors (static rule)."""
    try:
        from ky_core.macro import compute_compass, sector_playbook
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    compass = compute_compass(owner_id=owner_id)
    playbook = sector_playbook(compass.regime_hint)
    return _envelope({
        "regime": compass.regime_hint,
        "composite": round(compass.composite, 3),
        "playbook": playbook,
    })
