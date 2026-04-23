"""Execute router — live KIS quote / orderbook / investor / program endpoints."""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


# --------------------------------------------------------------------------- #
# Lazy adapter bootstrap                                                      #
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=1)
def _market():  # type: ignore[no-untyped-def]
    from ky_adapters.kis import KISMarketAdapter

    return KISMarketAdapter.from_settings()


@lru_cache(maxsize=1)
def _kis():  # type: ignore[no-untyped-def]
    from ky_adapters.kis import KISAdapter

    return KISAdapter.from_settings()


def _err(code: str, message: str, detail: dict | None = None) -> dict:
    return {"ok": False, "data": None, "error": {"code": code, "message": message, "detail": detail or {}}}


def _ok(data: Any) -> dict:
    return {"ok": True, "data": data, "error": None}


# --------------------------------------------------------------------------- #
# Routes                                                                      #
# --------------------------------------------------------------------------- #


@router.get("/health")
def execute_health() -> dict:
    """KIS backbone health (OAuth + shared token cache status)."""
    try:
        hc = _kis().healthcheck()
        return _ok(hc)
    except Exception as exc:  # pragma: no cover
        logger.exception("kis healthcheck failed")
        return _err("KIS_HEALTH_FAIL", str(exc))


@router.get("/overview")
def execute_overview() -> dict:
    """계좌 overview placeholder — returns KIS backbone status + account no.

    Real balance/positions require an account-scoped token flow which we'll
    wire in a later phase (inquire-balance TR). For now we surface the
    account number and health so the UI can stop showing the `_placeholder`.
    """
    kis = _kis()
    hc = kis.healthcheck()
    from ky_adapters.base import BaseAdapter

    return _ok({
        "account_no": BaseAdapter._env("KIS_ACCOUNT_NO"),
        "product_code": BaseAdapter._env("KIS_ACCOUNT_PRODUCT_CODE") or "01",
        "env": kis.env,
        "health": hc,
        "positions": [],
        "note": (
            "계좌 잔고는 별도 TR 연결 필요 (inquire-balance). "
            "현재는 KIS OAuth 토큰 상태만 노출."
        ),
    })


@router.get("/quote/{symbol}")
def execute_quote(symbol: str, market: str = "J") -> dict:
    """Current price snapshot (FHKST01010100)."""
    try:
        data = _market().get_quote(symbol, market=market)
        return _ok(data)
    except Exception as exc:
        logger.warning("quote fetch failed for %s: %s", symbol, exc)
        return _err("KIS_QUOTE_FAIL", str(exc), {"symbol": symbol})


@router.get("/orderbook/{symbol}")
def execute_orderbook(symbol: str, market: str = "J") -> dict:
    """10-level bid/ask ladder (FHKST01010200)."""
    try:
        data = _market().get_orderbook(symbol, market=market)
        return _ok(data)
    except Exception as exc:
        logger.warning("orderbook fetch failed for %s: %s", symbol, exc)
        return _err("KIS_ORDERBOOK_FAIL", str(exc), {"symbol": symbol})


@router.get("/investor/{symbol}")
def execute_investor(symbol: str, market: str = "J") -> dict:
    """Daily investor (개인/외국인/기관) net trade (FHKST01010900)."""
    try:
        rows = _market().get_investor_trend(symbol, market=market)
        return _ok({"rows": rows, "count": len(rows)})
    except Exception as exc:
        logger.warning("investor fetch failed for %s: %s", symbol, exc)
        return _err("KIS_INVESTOR_FAIL", str(exc), {"symbol": symbol})


@router.get("/program/{symbol}")
def execute_program_by_symbol(symbol: str, market: str = "J") -> dict:
    """Per-symbol program trade flow (FHPPG04650101)."""
    try:
        rows = _market().get_program_trade(symbol, market=market)
        return _ok({"rows": rows, "count": len(rows)})
    except Exception as exc:
        logger.warning("program fetch failed for %s: %s", symbol, exc)
        return _err("KIS_PROGRAM_FAIL", str(exc), {"symbol": symbol})


@router.get("/fluctuation")
def execute_fluctuation(
    market: str = "J",
    rank_sort: str = "0",
    top_n: int = 30,
) -> dict:
    """Top-N 등락률 ranking (FHPST01700000)."""
    try:
        rows = _market().get_fluctuation_ranking(
            market=market, rank_sort=rank_sort, top_n=top_n
        )
        return _ok({"rows": rows, "count": len(rows)})
    except Exception as exc:
        logger.warning("fluctuation fetch failed: %s", exc)
        return _err("KIS_FLUCTUATION_FAIL", str(exc))
