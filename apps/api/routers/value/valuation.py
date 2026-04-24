"""Valuation endpoints — DCF / WACC / EPS series / financial trend."""
from __future__ import annotations

from fastapi import APIRouter, Query

from routers.value._shared import DEFAULT_AS_OF, envelope, log

router = APIRouter()


@router.get("/dcf/{symbol}")
def dcf_endpoint(
    symbol: str,
    as_of: str = Query(DEFAULT_AS_OF),
    growth_high: float = Query(0.10, ge=-0.5, le=1.0),
    years_high: int = Query(5, ge=1, le=20),
    growth_term: float = Query(0.025, ge=0.0, le=0.1),
    wacc_override: float | None = Query(None, ge=0.01, le=0.5),
) -> dict:
    try:
        from ky_core.value import dcf as ky_dcf
        result = ky_dcf.dcf_value(
            symbol,
            as_of=as_of,
            growth_high=growth_high,
            years_high=years_high,
            growth_term=growth_term,
            wacc_override=wacc_override,
        )
    except Exception as exc:  # noqa: BLE001
        log.exception("dcf failed")
        return envelope(None, error={"code": "DCF_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return envelope(None, error={"code": "NO_DATA", "message": "no financials"}, ok=False)
    return envelope(result)


@router.get("/wacc/{symbol}")
def wacc_endpoint(
    symbol: str,
    as_of: str = Query(DEFAULT_AS_OF),
    rf: float = Query(0.030),
    erp: float = Query(0.060),
    beta: float = Query(1.0),
) -> dict:
    try:
        from ky_core.value import wacc as ky_wacc
        result = ky_wacc.wacc(symbol, as_of=as_of, rf=rf, erp=erp, beta=beta)
    except Exception as exc:  # noqa: BLE001
        log.exception("wacc failed")
        return envelope(None, error={"code": "WACC_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return envelope(None, error={"code": "NO_DATA", "message": "no financials"}, ok=False)
    return envelope(result)


@router.get("/eps/{symbol}")
def eps_series_endpoint(
    symbol: str,
    period: str = Query("Q", description="Q (quarterly) | A (annual) | ALL"),
    years: int = Query(5, ge=1, le=20),
    as_of: str | None = Query(None, description="ISO YYYY-MM-DD look-ahead cutoff"),
) -> dict:
    """Return the EPS history ported from Company_Credit's financial.db reader.

    Quarterly rows come from NaverComp's cF3002 snapshot (매핑된
    ``financial_statements_db`` 테이블).  Annual rows are available from 2021
    onward for most KOSPI constituents.  YoY is filled in automatically when
    the prior-year same-quarter / prior-year row exists.
    """
    try:
        from ky_core.value import eps_series as ky_eps
        points = ky_eps.get_eps_series(
            symbol, period=period, years=years, as_of=as_of
        )
    except Exception as exc:  # noqa: BLE001
        log.exception("eps_series failed")
        return envelope(None, error={"code": "EPS_FAILED", "message": str(exc)}, ok=False)
    if not points:
        return envelope(
            None,
            error={
                "code": "NO_DATA",
                "message": "no EPS rows in financial_statements_db or pit",
            },
            ok=False,
        )
    return envelope(
        {
            "symbol": symbol,
            "period": period,
            "years": years,
            "as_of": as_of,
            "n": len(points),
            "rows": [p.to_dict() for p in points],
        }
    )


@router.get("/trend/{symbol}")
def trend_endpoint(
    symbol: str,
    n: int = Query(8, ge=1, le=40),
    period_type: str = Query("Q", description="Q or FY"),
) -> dict:
    try:
        from ky_core.quant import pit as ky_pit
        from ky_core.storage import Repository
        repo = Repository()
        series = ky_pit.fin_series(repo, symbol, n=n, period_type=period_type)
        meta = ky_pit.universe_meta(repo, symbol)
    except Exception as exc:  # noqa: BLE001
        log.exception("trend failed")
        return envelope(None, error={"code": "TREND_FAILED", "message": str(exc)}, ok=False)
    return envelope({"symbol": symbol, "meta": meta, "series": series})
