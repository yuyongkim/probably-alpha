"""ky_adapters — external data source adapters.

Contract: every adapter inherits from :class:`ky_adapters.base.BaseAdapter` and
implements ``healthcheck`` / ``close``. Data-source policy (2026-04-22):

- KIS: single backbone for market data / orders (currently skeleton)
- DART: disclosures + PIT financials
- FRED / ECOS / KOSIS / EIA / EXIM: macro / FX / energy

Do NOT create Kiwoom, Yahoo, or Naver adapters — policy is KIS-only for quotes.
"""
from __future__ import annotations

from ky_adapters.base import (
    AdapterError,
    AuthError,
    BaseAdapter,
    HealthStatus,
    RateLimitError,
)

__version__ = "0.1.0"

__all__ = [
    "AdapterError",
    "AuthError",
    "BaseAdapter",
    "HealthStatus",
    "RateLimitError",
    "__version__",
]
