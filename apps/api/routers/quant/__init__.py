"""Quant router — factors / academic / smart-beta / PIT / IC / macro.

Structure:
    _shared.py  — envelope, markets CSV helper, DEFAULT_AS_OF, sys.path shim
    factors.py  — /factors, /academic/{strategy}, /smart_beta, /pit/{symbol},
                  /ic, /universe
    macro.py    — /macro/series, /macro/compass, /macro/regime,
                  /macro/corr, /macro/rotation
"""
from __future__ import annotations

from fastapi import APIRouter

from routers.quant.factors import router as _factors_router
from routers.quant.macro import router as _macro_router

router = APIRouter()
router.include_router(_factors_router)
router.include_router(_macro_router)
