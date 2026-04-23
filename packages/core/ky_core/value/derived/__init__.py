"""Derived value indicators — pure calculations on existing ky.db data.

No external fetches; every module reads only from the tables already
populated by the collectors:

- ``financials_pit``       — annual balance sheet + P&L (2,938 syms / 10y)
- ``fnguide_snapshots``    — payload JSON with margin, ROIC, debt ratio, DPS,
                             shares outstanding, per/pbr
- ``dividend_history``     — DART DPS annual history (per share_type)
- ``ohlcv``                — price time series (for DPS yield cross-check)
- ``universe``             — ticker → name/sector/market/industry

All modules expose a small, stable surface:

- ``<name>_for(symbol, *, repo=None, as_of=None)`` → single-symbol dict
- ``<name>_scan(*, repo=None, use_cache=True)``   → full-universe list

Scan helpers own their own (process-local) TTL cache so the web tier can
hit the API repeatedly without re-crunching 2k symbols.
"""
from __future__ import annotations

__all__ = [
    "dps",
    "piotroski_full",
    "altman_full",
    "moat_v2",
    "quality",
    "dividend_growth",
    "earnings_quality",
    "fcf_yield",
    "peg",
]
