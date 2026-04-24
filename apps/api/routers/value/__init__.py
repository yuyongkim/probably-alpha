"""Value router — DCF / WACC / trend / MoS / deep-value / Piotroski / Altman + FnGuide.

Structure:
    _shared.py     — envelope, logger, DEFAULT_AS_OF, sys.path shim
    valuation.py   — /dcf/*, /wacc/*, /eps/*, /trend/*
    screeners.py   — /mos, /deep_value, /evebitda, /roic, /piotroski, /altman
    fnguide.py     — /fnguide/{symbol} (10-min cache, graceful fallback)
    corp_actions.py— /insider, /buyback, /consensus, /moat, /segment,
                     /dividend, /comparables
    derived.py     — /dps, /dividend_growth*, /piotroski_full*, /altman_full*,
                     /moat_v2, /quality, /fcf_yield*, /earnings_quality*, /peg*
"""
from __future__ import annotations

from fastapi import APIRouter

from routers.value.corp_actions import router as _corp_actions_router
from routers.value.derived import router as _derived_router
from routers.value.fnguide import router as _fnguide_router
from routers.value.screeners import router as _screeners_router
from routers.value.valuation import router as _valuation_router

router = APIRouter()
router.include_router(_valuation_router)
router.include_router(_screeners_router)
router.include_router(_fnguide_router)
router.include_router(_corp_actions_router)
router.include_router(_derived_router)
