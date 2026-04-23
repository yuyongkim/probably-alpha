"""ky_core.macro — macro compass + regime detection.

Provides:

- :func:`compute_compass` — 4-axis scoring (growth / inflation / liquidity / credit)
  from the macro observations stored in ky.db.
- :func:`classify_regime` — maps compass output to Expansion / Slowdown /
  Recession / Recovery with rough probabilities.
- :func:`sector_playbook` — static mapping from regime → suggested sectors.

All computations read from :class:`ky_core.storage.Repository`. No external
calls; no heavy ML. Deterministic given the same inputs.
"""
from __future__ import annotations

from .compass import (
    AXIS_IDS,
    CompassResult,
    compute_compass,
    sector_playbook,
)
from .pickers import (
    CoverageReport,
    Observation,
    coverage_report,
    pick_indicator,
    pick_many,
)
from .regime import RegimeResult, classify_regime, regime_timeseries

__all__ = [
    "AXIS_IDS",
    "CompassResult",
    "CoverageReport",
    "Observation",
    "RegimeResult",
    "classify_regime",
    "compute_compass",
    "coverage_report",
    "pick_indicator",
    "pick_many",
    "regime_timeseries",
    "sector_playbook",
]
