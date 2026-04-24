"""Corporate-action / qualitative endpoints — insider / buyback / consensus /
moat / segment / dividend / comparables.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from routers.value._shared import envelope, log

router = APIRouter()


@router.get("/insider")
def insider_endpoint(
    lookback_days: int = Query(7, ge=1, le=90),
    kind: str = Query("all", description="all | insider | bulk | plan"),
    refresh: bool = Query(False, description="bypass in-memory cache"),
) -> dict:
    try:
        from ky_core.value import insider as ky_insider
        result = ky_insider.insider_summary(
            lookback_days=lookback_days,
            use_cache=not refresh,
        )
        if kind != "all":
            rows = ky_insider.recent_insider_filings(
                lookback_days=lookback_days,
                kind=kind,
                use_cache=not refresh,
            )
            result = {"kpi": result["kpi"], "rows": rows}
    except Exception as exc:  # noqa: BLE001
        log.exception("insider failed")
        return envelope(None, error={"code": "INSIDER_FAILED", "message": str(exc)}, ok=False)
    return envelope({"lookback_days": lookback_days, "kind": kind, **result})


@router.get("/buyback")
def buyback_endpoint(
    lookback_days: int = Query(30, ge=1, le=180),
    action: str = Query("all", description="all | buyback | dispose | cancel | trust"),
    refresh: bool = Query(False),
) -> dict:
    try:
        from ky_core.value import buyback as ky_buyback
        result = ky_buyback.buyback_summary(
            lookback_days=lookback_days,
            use_cache=not refresh,
        )
        if action != "all":
            rows = ky_buyback.recent_buyback_filings(
                lookback_days=lookback_days,
                action=action,
                use_cache=not refresh,
            )
            result = {"kpi": result["kpi"], "rows": rows}
    except Exception as exc:  # noqa: BLE001
        log.exception("buyback failed")
        return envelope(None, error={"code": "BUYBACK_FAILED", "message": str(exc)}, ok=False)
    return envelope({"lookback_days": lookback_days, "action": action, **result})


@router.get("/consensus")
def consensus_endpoint(
    mode: str = Query("eps_rev", description="eps_rev | tp_upside | recomm | summary"),
    n: int = Query(30, ge=1, le=200),
    refresh: bool = Query(False),
) -> dict:
    try:
        from ky_core.value import consensus as ky_consensus
        if mode == "summary":
            result = ky_consensus.consensus_summary(use_cache=not refresh)
        else:
            rows = ky_consensus.consensus_top(mode=mode, n=n, use_cache=not refresh)
            result = {"rows": rows, "n": len(rows)}
    except Exception as exc:  # noqa: BLE001
        log.exception("consensus failed")
        return envelope(None, error={"code": "CONSENSUS_FAILED", "message": str(exc)}, ok=False)
    return envelope({"mode": mode, **result})


@router.get("/moat")
def moat_endpoint(
    mode: str = Query("summary", description="summary | all | wide | narrow"),
    min_years: int = Query(5, ge=3, le=10),
    n: int = Query(100, ge=1, le=500),
    refresh: bool = Query(False),
) -> dict:
    try:
        from ky_core.value import moat as ky_moat
        rows = ky_moat.moat_scan(
            min_years=min_years,
            use_cache=not refresh,
        )
        summary = ky_moat.moat_summary(use_cache=not refresh)
        if mode in ("wide", "narrow"):
            rows = [r for r in rows if r["moat"] == mode]
        elif mode == "summary":
            return envelope({"mode": mode, **summary})
        return envelope({"mode": mode, "kpi": summary["kpi"], "rows": rows[:n]})
    except Exception as exc:  # noqa: BLE001
        log.exception("moat failed")
        return envelope(None, error={"code": "MOAT_FAILED", "message": str(exc)}, ok=False)


@router.get("/segment")
def segment_endpoint(refresh: bool = Query(False)) -> dict:
    try:
        from ky_core.value import segment as ky_segment
        result = ky_segment.segment_summary(use_cache=not refresh)
    except Exception as exc:  # noqa: BLE001
        log.exception("segment failed")
        return envelope(None, error={"code": "SEGMENT_FAILED", "message": str(exc)}, ok=False)
    return envelope(result)


@router.get("/dividend")
def dividend_endpoint(
    mode: str = Query("summary", description="summary | yield | aristocrat"),
    n: int = Query(30, ge=1, le=200),
    refresh: bool = Query(False),
) -> dict:
    try:
        from ky_core.value import dividend as ky_dividend
        if mode == "summary":
            result = ky_dividend.dividend_summary(use_cache=not refresh)
        else:
            rows = ky_dividend.dividend_top(mode=mode, n=n, use_cache=not refresh)
            result = {"rows": rows, "n": len(rows)}
    except Exception as exc:  # noqa: BLE001
        log.exception("dividend failed")
        return envelope(None, error={"code": "DIVIDEND_FAILED", "message": str(exc)}, ok=False)
    return envelope({"mode": mode, **result})


@router.get("/comparables")
def comparables_endpoint(
    sector: str | None = Query(None),
    mode: str = Query("summary", description="summary | by_sector | outliers"),
    n: int = Query(50, ge=1, le=500),
    refresh: bool = Query(False),
) -> dict:
    try:
        from ky_core.value import comparables as ky_comp
        if mode == "by_sector" and sector:
            rows = ky_comp.comparables_by_sector(sector, use_cache=not refresh)
            return envelope({"mode": mode, "sector": sector, "rows": rows[:n], "n": len(rows)})
        if mode == "outliers":
            rows = [r for r in ky_comp.comparables_scan(use_cache=not refresh) if r.get("outlier_cheap")]
            return envelope({"mode": mode, "rows": rows[:n], "n": len(rows)})
        summary = ky_comp.comparables_summary(use_cache=not refresh)
    except Exception as exc:  # noqa: BLE001
        log.exception("comparables failed")
        return envelope(None, error={"code": "COMPARABLES_FAILED", "message": str(exc)}, ok=False)
    return envelope({"mode": mode, **summary})
