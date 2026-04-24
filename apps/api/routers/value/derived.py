"""Derived indicators (``ky_core.value.derived.*``) — pure ky.db calcs.

Covers DPS / dividend growth / Piotroski-full / Altman-full / Moat v2 /
Quality / FCF Yield / Earnings Quality / PEG.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from routers.value._shared import envelope, log

router = APIRouter()


@router.get("/dps/{symbol}")
def dps_endpoint(symbol: str, years: int = Query(10, ge=1, le=30)) -> dict:
    try:
        from ky_core.value.derived import dps as ky_dps
        result = ky_dps.dps_for(symbol, years=years)
    except Exception as exc:  # noqa: BLE001
        log.exception("dps failed")
        return envelope(None, error={"code": "DPS_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return envelope(None, error={"code": "NO_DATA", "message": "no dps history"}, ok=False)
    return envelope(result)


@router.get("/dividend_growth/{symbol}")
def dividend_growth_endpoint(symbol: str, years: int = Query(5, ge=3, le=10)) -> dict:
    try:
        from ky_core.value.derived import dividend_growth as ky_dg
        result = ky_dg.dividend_growth_for(symbol, years=years)
    except Exception as exc:  # noqa: BLE001
        log.exception("dividend_growth failed")
        return envelope(None, error={"code": "DGROWTH_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return envelope(None, error={"code": "NO_DATA", "message": "no dps / ni series"}, ok=False)
    return envelope(result)


@router.get("/dividend_growth")
def dividend_growth_top_endpoint(
    n: int = Query(50, ge=1, le=200),
    years: int = Query(5, ge=3, le=10),
) -> dict:
    try:
        from ky_core.value.derived import dividend_growth as ky_dg
        rows = ky_dg.dividend_growth_scan(years=years)[:n]
    except Exception as exc:  # noqa: BLE001
        log.exception("dividend_growth top failed")
        return envelope(None, error={"code": "DGROWTH_FAILED", "message": str(exc)}, ok=False)
    return envelope({"n": len(rows), "years": years, "rows": rows})


@router.get("/piotroski_full/{symbol}")
def piotroski_full_endpoint(symbol: str) -> dict:
    try:
        from ky_core.value.derived import piotroski_full as ky_p
        result = ky_p.piotroski_full_for(symbol)
    except Exception as exc:  # noqa: BLE001
        log.exception("piotroski_full failed")
        return envelope(None, error={"code": "PIOTROSKI_FULL_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return envelope(None, error={"code": "NO_DATA", "message": "no fy rows"}, ok=False)
    return envelope(result)


@router.get("/piotroski_full")
def piotroski_full_top_endpoint(n: int = Query(50, ge=1, le=200)) -> dict:
    try:
        from ky_core.value.derived import piotroski_full as ky_p
        rows = ky_p.piotroski_full_scan()[:n]
    except Exception as exc:  # noqa: BLE001
        log.exception("piotroski_full scan failed")
        return envelope(None, error={"code": "PIOTROSKI_FULL_FAILED", "message": str(exc)}, ok=False)
    return envelope({"n": len(rows), "rows": rows})


@router.get("/altman_full/{symbol}")
def altman_full_endpoint(symbol: str) -> dict:
    try:
        from ky_core.value.derived import altman_full as ky_a
        result = ky_a.altman_full_for(symbol)
    except Exception as exc:  # noqa: BLE001
        log.exception("altman_full failed")
        return envelope(None, error={"code": "ALTMAN_FULL_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return envelope(None, error={"code": "NO_DATA", "message": "no balance sheet"}, ok=False)
    return envelope(result)


@router.get("/altman_full")
def altman_full_top_endpoint(
    n: int = Query(50, ge=1, le=500),
    zone: str = Query("safe", description="safe | grey | distress | all"),
) -> dict:
    try:
        from ky_core.value.derived import altman_full as ky_a
        rows = ky_a.altman_full_scan()
        if zone != "all":
            rows = [r for r in rows if r["zone"] == zone]
        kpi = {
            "safe": sum(1 for r in rows if r["zone"] == "safe"),
            "grey": sum(1 for r in rows if r["zone"] == "grey"),
            "distress": sum(1 for r in rows if r["zone"] == "distress"),
        }
    except Exception as exc:  # noqa: BLE001
        log.exception("altman_full top failed")
        return envelope(None, error={"code": "ALTMAN_FULL_FAILED", "message": str(exc)}, ok=False)
    return envelope({"zone": zone, "kpi": kpi, "n": min(n, len(rows)), "rows": rows[:n]})


@router.get("/moat_v2")
def moat_v2_endpoint(
    mode: str = Query("summary", description="summary | wide | narrow | all"),
    n: int = Query(100, ge=1, le=500),
) -> dict:
    try:
        from ky_core.value.derived import moat_v2 as ky_m
        summary = ky_m.moat_v2_summary()
        if mode == "summary":
            return envelope({"mode": mode, **summary})
        rows = ky_m.moat_v2_scan()
        if mode in ("wide", "narrow"):
            rows = [r for r in rows if r["moat_grade"] == mode]
    except Exception as exc:  # noqa: BLE001
        log.exception("moat_v2 failed")
        return envelope(None, error={"code": "MOAT_V2_FAILED", "message": str(exc)}, ok=False)
    return envelope({"mode": mode, "kpi": summary["kpi"], "rows": rows[:n]})


@router.get("/quality")
def quality_endpoint(top_n: int = Query(50, ge=1, le=200)) -> dict:
    try:
        from ky_core.value.derived import quality as ky_q
        rows = ky_q.quality_top(n=top_n)
    except Exception as exc:  # noqa: BLE001
        log.exception("quality failed")
        return envelope(None, error={"code": "QUALITY_FAILED", "message": str(exc)}, ok=False)
    return envelope({"n": len(rows), "rows": rows})


@router.get("/fcf_yield/{symbol}")
def fcf_yield_symbol_endpoint(symbol: str) -> dict:
    try:
        from ky_core.value.derived import fcf_yield as ky_f
        result = ky_f.fcf_yield_for(symbol)
    except Exception as exc:  # noqa: BLE001
        log.exception("fcf_yield failed")
        return envelope(None, error={"code": "FCF_YIELD_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return envelope(None, error={"code": "NO_DATA", "message": "no market cap / fin"}, ok=False)
    return envelope(result)


@router.get("/fcf_yield")
def fcf_yield_top_endpoint(top_n: int = Query(50, ge=1, le=200)) -> dict:
    try:
        from ky_core.value.derived import fcf_yield as ky_f
        rows = ky_f.fcf_yield_top(n=top_n)
    except Exception as exc:  # noqa: BLE001
        log.exception("fcf_yield top failed")
        return envelope(None, error={"code": "FCF_YIELD_FAILED", "message": str(exc)}, ok=False)
    return envelope({"n": len(rows), "rows": rows})


@router.get("/earnings_quality/{symbol}")
def earnings_quality_symbol_endpoint(symbol: str) -> dict:
    try:
        from ky_core.value.derived import earnings_quality as ky_eq
        result = ky_eq.earnings_quality_for(symbol)
    except Exception as exc:  # noqa: BLE001
        log.exception("earnings_quality failed")
        return envelope(None, error={"code": "EQ_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return envelope(None, error={"code": "NO_DATA", "message": "need 2 fy rows"}, ok=False)
    return envelope(result)


@router.get("/earnings_quality")
def earnings_quality_top_endpoint(
    bucket: str = Query("high", description="high | low | all"),
    n: int = Query(50, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value.derived import earnings_quality as ky_eq
        if bucket == "all":
            rows = ky_eq.earnings_quality_scan()[:n]
        else:
            rows = ky_eq.earnings_quality_top(bucket=bucket, n=n)
    except Exception as exc:  # noqa: BLE001
        log.exception("earnings_quality top failed")
        return envelope(None, error={"code": "EQ_FAILED", "message": str(exc)}, ok=False)
    return envelope({"bucket": bucket, "n": len(rows), "rows": rows})


@router.get("/peg/{symbol}")
def peg_symbol_endpoint(symbol: str) -> dict:
    try:
        from ky_core.value.derived import peg as ky_peg
        result = ky_peg.peg_for(symbol)
    except Exception as exc:  # noqa: BLE001
        log.exception("peg failed")
        return envelope(None, error={"code": "PEG_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return envelope(None, error={"code": "NO_DATA", "message": "per missing or negative growth"}, ok=False)
    return envelope(result)


@router.get("/peg")
def peg_top_endpoint(limit: int = Query(50, ge=1, le=200)) -> dict:
    try:
        from ky_core.value.derived import peg as ky_peg
        rows = ky_peg.peg_cheap_growth(limit=limit)
    except Exception as exc:  # noqa: BLE001
        log.exception("peg top failed")
        return envelope(None, error={"code": "PEG_FAILED", "message": str(exc)}, ok=False)
    return envelope({"n": len(rows), "rows": rows})
