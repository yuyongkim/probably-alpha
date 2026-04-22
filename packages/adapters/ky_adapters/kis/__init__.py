"""KIS (Korea Investment & Securities) adapter — skeleton only.

Real API calls are intentionally not implemented until KIS credentials are
provisioned in ``~/.ky-platform/shared.env``.
"""
from __future__ import annotations

from ky_adapters.kis.client import KISAdapter

__all__ = ["KISAdapter"]
