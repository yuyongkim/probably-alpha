"""Macro endpoints — series / compass / regime / correlation / rotation."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Query

from routers.quant._shared import envelope, log

router = APIRouter()


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
        return envelope({
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
        return envelope(None, error={"code": "STORAGE_READ_FAILED", "message": str(exc)}, ok=False)

    warning = None
    if not rows:
        warning = (
            "No observations in SQLite yet. Run: "
            "python scripts/collect.py --source all-macro"
        )

    return envelope({
        "source": source,
        "series_id": series_id,
        "observations": rows,
        "stale_data": bool(warning),
        "warning": warning,
    })


@router.get("/macro/compass")
def macro_compass(owner_id: str = Query("self")) -> dict:
    """Return the 4-axis compass + current regime hint."""
    try:
        from ky_core.macro import compute_compass, sector_playbook
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    res = compute_compass(owner_id=owner_id)
    return envelope({
        **res.to_dict(),
        "playbook": sector_playbook(res.regime_hint),
    })


@router.get("/macro/regime")
def macro_regime(owner_id: str = Query("self")) -> dict:
    """Return 4-state regime probabilities + 12-month history."""
    try:
        from ky_core.macro import classify_regime
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    res = classify_regime(owner_id=owner_id)
    return envelope(res.to_dict())


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
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)

    repo = Repository(owner_id=owner_id)
    try:
        cells = _build_corr_cells(repo, get_engine(), window=window)
    except Exception as exc:  # noqa: BLE001
        log.exception("corr build failed")
        return envelope(None, error={"code": "COMPUTE_FAILED", "message": str(exc)}, ok=False)
    return envelope(cells)


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


@router.get("/macro/rotation")
def macro_rotation(owner_id: str = Query("self")) -> dict:
    """Current regime → recommended sectors (static rule)."""
    try:
        from ky_core.macro import compute_compass, sector_playbook
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    compass = compute_compass(owner_id=owner_id)
    playbook = sector_playbook(compass.regime_hint)
    return envelope({
        "regime": compass.regime_hint,
        "composite": round(compass.composite, 3),
        "playbook": playbook,
    })
