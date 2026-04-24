"""Screener endpoints — MoS / Deep Value / EV-EBITDA / ROIC / Piotroski / Altman."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from routers.value._shared import DEFAULT_AS_OF, envelope, log

router = APIRouter()


@router.get("/mos")
def mos_endpoint(
    as_of: str = Query(DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import safety as ky_safety
        rows = ky_safety.mos_leaderboard(as_of=as_of, n=n)
    except Exception as exc:  # noqa: BLE001
        log.exception("mos failed")
        return envelope(None, error={"code": "MOS_FAILED", "message": str(exc)}, ok=False)
    return envelope({"as_of": as_of, "n": len(rows), "rows": rows})


@router.get("/deep_value")
def deep_value_endpoint(
    as_of: str = Query(DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import safety as ky_safety
        rows = ky_safety.deep_value_leaderboard(as_of=as_of, n=n)
    except Exception as exc:  # noqa: BLE001
        log.exception("deep_value failed")
        return envelope(None, error={"code": "DEEP_VALUE_FAILED", "message": str(exc)}, ok=False)
    return envelope({"as_of": as_of, "n": len(rows), "rows": rows})


@router.get("/evebitda")
def evebitda_endpoint(
    as_of: str = Query(DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import valuation as ky_val
        rows = ky_val.evebitda_leaderboard(as_of=as_of, n=n)
    except Exception as exc:  # noqa: BLE001
        log.exception("evebitda failed")
        return envelope(None, error={"code": "EVEBITDA_FAILED", "message": str(exc)}, ok=False)
    return envelope({"as_of": as_of, "n": len(rows), "rows": rows})


@router.get("/roic")
def roic_endpoint(
    as_of: str = Query(DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
    mode: str = Query("roic", description="roic | fcf_yield"),
) -> dict:
    try:
        from ky_core.value import valuation as ky_val
        if mode == "fcf_yield":
            rows = ky_val.fcf_yield_leaderboard(as_of=as_of, n=n)
        else:
            rows = ky_val.roic_leaderboard(as_of=as_of, n=n)
    except Exception as exc:  # noqa: BLE001
        log.exception("roic failed")
        return envelope(None, error={"code": "ROIC_FAILED", "message": str(exc)}, ok=False)
    return envelope({"as_of": as_of, "mode": mode, "n": len(rows), "rows": rows})


@router.get("/piotroski")
def piotroski_endpoint(
    symbol: str | None = Query(None, description="single symbol or omit for batch top"),
    as_of: str = Query(DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import piotroski as ky_piotroski
        from ky_core.quant import factors as ky_factors
        if symbol:
            result = ky_piotroski.piotroski_score(symbol, as_of=as_of)
            if result is None:
                return envelope(None, error={"code": "NO_DATA", "message": "no financials"}, ok=False)
            return envelope(result)
        # batch top — score everything with ≥ 4 flags present
        rows = ky_factors.scan(as_of)
        scored: list[dict[str, Any]] = []
        for r in rows[:600]:
            p = ky_piotroski.piotroski_score(r["symbol"], as_of=as_of)
            if p and p["max_possible"] >= 3:
                scored.append({**r, **p})
        scored.sort(key=lambda x: (x["score"], x["max_possible"]), reverse=True)
        return envelope({"as_of": as_of, "n": min(n, len(scored)), "rows": scored[:n]})
    except Exception as exc:  # noqa: BLE001
        log.exception("piotroski failed")
        return envelope(None, error={"code": "PIOTROSKI_FAILED", "message": str(exc)}, ok=False)


@router.get("/altman")
def altman_endpoint(
    symbol: str | None = Query(None, description="single symbol or omit for batch safe/grey/distress"),
    as_of: str = Query(DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import altman as ky_altman
        from ky_core.quant import factors as ky_factors
        if symbol:
            result = ky_altman.altman_z(symbol, as_of=as_of)
            if result is None:
                return envelope(None, error={"code": "NO_DATA", "message": "no financials"}, ok=False)
            return envelope(result)
        rows = ky_factors.scan(as_of)
        scored: list[dict[str, Any]] = []
        for r in rows[:600]:
            z = ky_altman.altman_z(r["symbol"], as_of=as_of)
            if z:
                scored.append({**r, **z})
        scored.sort(key=lambda x: x["z_score"], reverse=True)
        return envelope({"as_of": as_of, "n": min(n, len(scored)), "rows": scored[:n]})
    except Exception as exc:  # noqa: BLE001
        log.exception("altman failed")
        return envelope(None, error={"code": "ALTMAN_FAILED", "message": str(exc)}, ok=False)
