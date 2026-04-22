"""ky_core.scanning — Chartist real-data scanning layer.

Provides end-of-day (EOD) scans over the ky.db OHLCV + universe tables:
- Trend Template (Minervini SEPA) evaluation
- Leader score composition (TT/RS/VCP/EPS/Sector)
- Sector strength scoreboard
- 52-week breakouts
- Market breadth (A/D, %>MA, new H/L, Up-vol, McClellan)
- 6 Market Wizards presets (Minervini, O'Neil, Darvas, Livermore, Zanger, Weinstein)

All modules read through ``ky_core.scanning.loader`` which caches a single
wide panel of the last ~250 trading days so a single /today request issues
one bulk SQL query instead of N per-symbol round trips.
"""
from __future__ import annotations

from ky_core.scanning.leader_scan import Leader, scan_leaders
from ky_core.scanning.sepa import TrendTemplate, count_passes, evaluate
from ky_core.scanning.sector_strength import SectorStrength, sector_strength
from ky_core.scanning.breakouts import BreakoutRow, scan_breakouts
from ky_core.scanning.breadth import BreadthSnapshot, compute_breadth
from ky_core.scanning.vcp import VCPStatus, detect_vcp

__all__ = [
    "Leader",
    "scan_leaders",
    "TrendTemplate",
    "evaluate",
    "count_passes",
    "SectorStrength",
    "sector_strength",
    "BreakoutRow",
    "scan_breakouts",
    "BreadthSnapshot",
    "compute_breadth",
    "VCPStatus",
    "detect_vcp",
]
