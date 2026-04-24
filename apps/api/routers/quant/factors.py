"""Factor / academic / smart-beta / PIT / IC / universe endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query

from routers.quant._shared import DEFAULT_AS_OF, envelope, log, markets

router = APIRouter()


@router.get("/factors")
def factors(
    as_of: str = Query(DEFAULT_AS_OF, description="YYYY-MM-DD"),
    market: str = Query("KOSPI,KOSDAQ"),
    sort: str = Query("composite", description="composite|momentum|value|quality|low_vol|growth"),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """Universe-wide factor scan with percentile ranks."""
    try:
        from ky_core.quant import factors as ky_factors
        rows = ky_factors.scan(as_of, markets(market))
    except Exception as exc:  # noqa: BLE001
        log.exception("factor scan failed")
        return envelope(None, error={"code": "FACTOR_SCAN_FAILED", "message": str(exc)}, ok=False)
    if sort != "composite":
        rows = [r for r in rows if r.get(sort) is not None]
        rows.sort(key=lambda r: r[sort], reverse=True)
    rows = rows[:limit]
    return envelope({"as_of": as_of, "sort": sort, "n": len(rows), "rows": rows})


@router.get("/academic/{strategy}")
def academic_endpoint(
    strategy: str,
    as_of: str = Query(DEFAULT_AS_OF),
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
            return envelope(None, error={
                "code": "UNKNOWN_STRATEGY",
                "message": f"{strategy} not in magic_formula|deep_value|fast_growth|super_quant",
            }, ok=False)
    except Exception as exc:  # noqa: BLE001
        log.exception("academic strategy failed")
        return envelope(None, error={"code": "ACADEMIC_FAILED", "message": str(exc)}, ok=False)
    return envelope({"as_of": as_of, "strategy": strategy, "n": len(rows), "rows": rows})


@router.get("/smart_beta")
def smart_beta(
    variant: str = Query("equal_weight"),
    as_of: str = Query(DEFAULT_AS_OF),
    n: int = Query(50, ge=1, le=200),
) -> dict:
    try:
        from ky_core.quant import smart_beta as ky_smart_beta
        bundle = ky_smart_beta.build(variant, as_of=as_of, n=n)
    except ValueError as exc:
        return envelope(None, error={"code": "UNKNOWN_VARIANT", "message": str(exc)}, ok=False)
    except Exception as exc:  # noqa: BLE001
        log.exception("smart beta build failed")
        return envelope(None, error={"code": "SMART_BETA_FAILED", "message": str(exc)}, ok=False)
    return envelope(bundle)


@router.get("/pit/{symbol}")
def pit_endpoint(
    symbol: str,
    as_of: str = Query(DEFAULT_AS_OF),
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
        return envelope(None, error={"code": "PIT_FAILED", "message": str(exc)}, ok=False)
    return envelope({"symbol": symbol, "as_of": as_of, "meta": meta, "ttm": ttm, "series": series})


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
        return envelope(None, error={"code": "IC_FAILED", "message": str(exc)}, ok=False)
    return envelope(result)


@router.get("/universe")
def universe(
    market: str = Query("KOSPI,KOSDAQ"),
    limit: int = Query(500, ge=1, le=5000),
) -> dict:
    try:
        from ky_core.quant import factors as ky_factors
        from ky_core.storage import Repository
        repo = Repository()
        rows = ky_factors._load_universe(repo, markets(market))[:limit]
    except Exception as exc:  # noqa: BLE001
        log.exception("universe load failed")
        return envelope(None, error={"code": "UNIVERSE_FAILED", "message": str(exc)}, ok=False)
    return envelope({"market": markets(market), "n": len(rows), "rows": rows})
