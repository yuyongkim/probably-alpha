"""KIS (Korea Investment & Securities) adapter — activated 2026-04-22.

Real OAuth2 token issuance and authenticated REST calls are enabled.
Credentials are loaded from ``~/.ky-platform/shared.env``.
"""
from __future__ import annotations

from ky_adapters.kis.client import KISAdapter
from ky_adapters.kis.finance import (
    KIS_ENDPOINTS,
    KIS_OUTPUT_MAP,
    KISFinanceAdapter,
    KISFinanceEndpoint,
)
from ky_adapters.kis.market import (
    KIS_MARKET_ENDPOINTS,
    KISMarketAdapter,
    KISMarketEndpoint,
)

__all__ = [
    "KISAdapter",
    "KISFinanceAdapter",
    "KISFinanceEndpoint",
    "KIS_ENDPOINTS",
    "KIS_OUTPUT_MAP",
    "KISMarketAdapter",
    "KISMarketEndpoint",
    "KIS_MARKET_ENDPOINTS",
]
