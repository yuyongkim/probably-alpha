"""Value router — DCF / WACC / trend / MoS / deep-value / Piotroski / Altman + FnGuide."""
from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Query

# Make packages/core & packages/adapters importable without `pip install -e .`
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
_PKG_ADAPTERS = Path(__file__).resolve().parents[4] / "packages" / "adapters"
for _p in (_PKG_CORE, _PKG_ADAPTERS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

router = APIRouter()
log = logging.getLogger(__name__)

_DEFAULT_AS_OF = "2026-04-17"


def _envelope(data: Any = None, error: Any = None, ok: Optional[bool] = None) -> dict[str, Any]:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}


# --------------------------------------------------------------------------- #
# DCF                                                                         #
# --------------------------------------------------------------------------- #


@router.get("/dcf/{symbol}")
def dcf_endpoint(
    symbol: str,
    as_of: str = Query(_DEFAULT_AS_OF),
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
        return _envelope(None, error={"code": "DCF_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return _envelope(None, error={"code": "NO_DATA", "message": "no financials"}, ok=False)
    return _envelope(result)


# --------------------------------------------------------------------------- #
# WACC                                                                        #
# --------------------------------------------------------------------------- #


@router.get("/wacc/{symbol}")
def wacc_endpoint(
    symbol: str,
    as_of: str = Query(_DEFAULT_AS_OF),
    rf: float = Query(0.030),
    erp: float = Query(0.060),
    beta: float = Query(1.0),
) -> dict:
    try:
        from ky_core.value import wacc as ky_wacc
        result = ky_wacc.wacc(symbol, as_of=as_of, rf=rf, erp=erp, beta=beta)
    except Exception as exc:  # noqa: BLE001
        log.exception("wacc failed")
        return _envelope(None, error={"code": "WACC_FAILED", "message": str(exc)}, ok=False)
    if not result:
        return _envelope(None, error={"code": "NO_DATA", "message": "no financials"}, ok=False)
    return _envelope(result)


# --------------------------------------------------------------------------- #
# EPS time-series                                                             #
# --------------------------------------------------------------------------- #


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
        return _envelope(None, error={"code": "EPS_FAILED", "message": str(exc)}, ok=False)
    if not points:
        return _envelope(
            None,
            error={
                "code": "NO_DATA",
                "message": "no EPS rows in financial_statements_db or pit",
            },
            ok=False,
        )
    return _envelope(
        {
            "symbol": symbol,
            "period": period,
            "years": years,
            "as_of": as_of,
            "n": len(points),
            "rows": [p.to_dict() for p in points],
        }
    )


# --------------------------------------------------------------------------- #
# Financial trend                                                             #
# --------------------------------------------------------------------------- #


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
        return _envelope(None, error={"code": "TREND_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"symbol": symbol, "meta": meta, "series": series})


# --------------------------------------------------------------------------- #
# Margin of Safety leaderboard                                                #
# --------------------------------------------------------------------------- #


@router.get("/mos")
def mos_endpoint(
    as_of: str = Query(_DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import safety as ky_safety
        rows = ky_safety.mos_leaderboard(as_of=as_of, n=n)
    except Exception as exc:  # noqa: BLE001
        log.exception("mos failed")
        return _envelope(None, error={"code": "MOS_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"as_of": as_of, "n": len(rows), "rows": rows})


# --------------------------------------------------------------------------- #
# Deep-value screener                                                         #
# --------------------------------------------------------------------------- #


@router.get("/deep_value")
def deep_value_endpoint(
    as_of: str = Query(_DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import safety as ky_safety
        rows = ky_safety.deep_value_leaderboard(as_of=as_of, n=n)
    except Exception as exc:  # noqa: BLE001
        log.exception("deep_value failed")
        return _envelope(None, error={"code": "DEEP_VALUE_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"as_of": as_of, "n": len(rows), "rows": rows})


# --------------------------------------------------------------------------- #
# EV / EBITDA leaderboard                                                     #
# --------------------------------------------------------------------------- #


@router.get("/evebitda")
def evebitda_endpoint(
    as_of: str = Query(_DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import valuation as ky_val
        rows = ky_val.evebitda_leaderboard(as_of=as_of, n=n)
    except Exception as exc:  # noqa: BLE001
        log.exception("evebitda failed")
        return _envelope(None, error={"code": "EVEBITDA_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"as_of": as_of, "n": len(rows), "rows": rows})


# --------------------------------------------------------------------------- #
# ROIC / FCF Yield                                                            #
# --------------------------------------------------------------------------- #


@router.get("/roic")
def roic_endpoint(
    as_of: str = Query(_DEFAULT_AS_OF),
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
        return _envelope(None, error={"code": "ROIC_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"as_of": as_of, "mode": mode, "n": len(rows), "rows": rows})


# --------------------------------------------------------------------------- #
# Piotroski F-Score                                                           #
# --------------------------------------------------------------------------- #


@router.get("/piotroski")
def piotroski_endpoint(
    symbol: str | None = Query(None, description="single symbol or omit for batch top"),
    as_of: str = Query(_DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import piotroski as ky_piotroski
        from ky_core.quant import factors as ky_factors
        if symbol:
            result = ky_piotroski.piotroski_score(symbol, as_of=as_of)
            if result is None:
                return _envelope(None, error={"code": "NO_DATA", "message": "no financials"}, ok=False)
            return _envelope(result)
        # batch top — score everything with ≥ 4 flags present
        rows = ky_factors.scan(as_of)
        scored: list[dict[str, Any]] = []
        for r in rows[:600]:
            p = ky_piotroski.piotroski_score(r["symbol"], as_of=as_of)
            if p and p["max_possible"] >= 3:
                scored.append({**r, **p})
        scored.sort(key=lambda x: (x["score"], x["max_possible"]), reverse=True)
        return _envelope({"as_of": as_of, "n": min(n, len(scored)), "rows": scored[:n]})
    except Exception as exc:  # noqa: BLE001
        log.exception("piotroski failed")
        return _envelope(None, error={"code": "PIOTROSKI_FAILED", "message": str(exc)}, ok=False)


# --------------------------------------------------------------------------- #
# Altman Z-Score                                                              #
# --------------------------------------------------------------------------- #


@router.get("/altman")
def altman_endpoint(
    symbol: str | None = Query(None, description="single symbol or omit for batch safe/grey/distress"),
    as_of: str = Query(_DEFAULT_AS_OF),
    n: int = Query(30, ge=1, le=200),
) -> dict:
    try:
        from ky_core.value import altman as ky_altman
        from ky_core.quant import factors as ky_factors
        if symbol:
            result = ky_altman.altman_z(symbol, as_of=as_of)
            if result is None:
                return _envelope(None, error={"code": "NO_DATA", "message": "no financials"}, ok=False)
            return _envelope(result)
        rows = ky_factors.scan(as_of)
        scored: list[dict[str, Any]] = []
        for r in rows[:600]:
            z = ky_altman.altman_z(r["symbol"], as_of=as_of)
            if z:
                scored.append({**r, **z})
        scored.sort(key=lambda x: x["z_score"], reverse=True)
        return _envelope({"as_of": as_of, "n": min(n, len(scored)), "rows": scored[:n]})
    except Exception as exc:  # noqa: BLE001
        log.exception("altman failed")
        return _envelope(None, error={"code": "ALTMAN_FAILED", "message": str(exc)}, ok=False)


# --------------------------------------------------------------------------- #
# FnGuide snapshot — Naver + comp.fnguide.com fundamentals                    #
# --------------------------------------------------------------------------- #


FNGUIDE_CACHE_TTL_SEC = 600  # 10 minutes per symbol


@router.get("/fnguide/{symbol}")
def fnguide_endpoint(
    symbol: str,
    refresh: bool = Query(False, description="force re-fetch ignoring cache"),
) -> dict:
    """Return the cached/fresh FnGuide snapshot for ``symbol``.

    Cache lifetime: 10 minutes. Backing store: ``fnguide_snapshots`` table in
    ky.db. When refresh=true we ignore cache age but still persist so future
    callers benefit.
    """
    try:
        from ky_core.storage import Repository
        repo = Repository()
    except Exception as exc:  # noqa: BLE001
        log.exception("fnguide: repo unavailable")
        return _envelope(
            None,
            error={"code": "STORAGE_UNAVAILABLE", "message": str(exc)},
            ok=False,
        )

    cached = repo.get_fnguide_snapshot(symbol)
    if cached and not refresh:
        fetched_iso = cached.get("fetched_at") or ""
        try:
            fetched_dt = datetime.fromisoformat(fetched_iso) if fetched_iso else None
        except ValueError:
            fetched_dt = None
        age = (
            (datetime.utcnow() - fetched_dt).total_seconds()
            if fetched_dt
            else FNGUIDE_CACHE_TTL_SEC + 1
        )
        if age <= FNGUIDE_CACHE_TTL_SEC:
            try:
                payload = json.loads(cached["payload"])
            except Exception:  # noqa: BLE001
                payload = None
            if payload:
                return _envelope({
                    **payload,
                    "cached": True,
                    "age_seconds": int(age),
                })

    try:
        from ky_adapters.naver_fnguide import FnguideAdapter
        adapter = FnguideAdapter.from_settings()
        # Enriched bundle: Mobile (integration + finance + trend) + NaverComp
        # (cF3002 / cF4002 / cF9001 / ownership). Runs in-parallel internally.
        snapshot = adapter.get_full_snapshot(symbol)
        adapter.close()
    except Exception as exc:  # noqa: BLE001
        log.exception("fnguide: fetch failed for %s", symbol)
        # Degrade gracefully — if we have *any* cache at all, serve it with a flag.
        if cached:
            try:
                payload = json.loads(cached["payload"])
                return _envelope({
                    **payload,
                    "cached": True,
                    "stale": True,
                    "fetch_error": f"{type(exc).__name__}: {exc}",
                })
            except Exception:  # noqa: BLE001
                pass
        return _envelope(
            None,
            error={"code": "FNGUIDE_FAILED", "message": str(exc)},
            ok=False,
        )

    payload = snapshot.to_dict()
    try:
        repo.upsert_fnguide_snapshot(
            symbol,
            json.dumps(payload, ensure_ascii=False),
            source=snapshot.source,
            degraded=snapshot.degraded,
        )
    except Exception:  # noqa: BLE001
        log.exception("fnguide: persist failed for %s", symbol)

    return _envelope({**payload, "cached": False, "age_seconds": 0})


# --------------------------------------------------------------------------- #
# Insider trading (DART 임원·주요주주)                                        #
# --------------------------------------------------------------------------- #


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
        return _envelope(None, error={"code": "INSIDER_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"lookback_days": lookback_days, "kind": kind, **result})


# --------------------------------------------------------------------------- #
# Buyback / Treasury shares                                                   #
# --------------------------------------------------------------------------- #


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
        return _envelope(None, error={"code": "BUYBACK_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"lookback_days": lookback_days, "action": action, **result})


# --------------------------------------------------------------------------- #
# Analyst consensus                                                           #
# --------------------------------------------------------------------------- #


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
        return _envelope(None, error={"code": "CONSENSUS_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"mode": mode, **result})


# --------------------------------------------------------------------------- #
# Economic moat                                                               #
# --------------------------------------------------------------------------- #


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
            return _envelope({"mode": mode, **summary})
        return _envelope({"mode": mode, "kpi": summary["kpi"], "rows": rows[:n]})
    except Exception as exc:  # noqa: BLE001
        log.exception("moat failed")
        return _envelope(None, error={"code": "MOAT_FAILED", "message": str(exc)}, ok=False)


# --------------------------------------------------------------------------- #
# Segment / SOTP                                                              #
# --------------------------------------------------------------------------- #


@router.get("/segment")
def segment_endpoint(refresh: bool = Query(False)) -> dict:
    try:
        from ky_core.value import segment as ky_segment
        result = ky_segment.segment_summary(use_cache=not refresh)
    except Exception as exc:  # noqa: BLE001
        log.exception("segment failed")
        return _envelope(None, error={"code": "SEGMENT_FAILED", "message": str(exc)}, ok=False)
    return _envelope(result)


# --------------------------------------------------------------------------- #
# Dividend                                                                    #
# --------------------------------------------------------------------------- #


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
        return _envelope(None, error={"code": "DIVIDEND_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"mode": mode, **result})


# --------------------------------------------------------------------------- #
# Comparables / peer valuation                                                #
# --------------------------------------------------------------------------- #


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
            return _envelope({"mode": mode, "sector": sector, "rows": rows[:n], "n": len(rows)})
        if mode == "outliers":
            rows = [r for r in ky_comp.comparables_scan(use_cache=not refresh) if r.get("outlier_cheap")]
            return _envelope({"mode": mode, "rows": rows[:n], "n": len(rows)})
        summary = ky_comp.comparables_summary(use_cache=not refresh)
    except Exception as exc:  # noqa: BLE001
        log.exception("comparables failed")
        return _envelope(None, error={"code": "COMPARABLES_FAILED", "message": str(exc)}, ok=False)
    return _envelope({"mode": mode, **summary})


# Silence unused import warning — time used indirectly (re-exports).
_ = time
