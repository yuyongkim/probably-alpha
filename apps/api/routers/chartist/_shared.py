"""Shared helpers for chartist sub-routers.

Keeps the lazy scanning-module loader + response envelope in one place so
every sub-router (leaders, technicals, wizards, korea) picks them up
without duplicating the sys.path / import shim.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Make packages/core importable without requiring `pip install -e .`
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))


def envelope(data: Any = None, error: Any = None, ok: bool | None = None) -> dict:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}


def scanning() -> dict:
    """Lazily import all ky_core.scanning submodules used by this router."""
    # Import submodules directly to avoid the parent package ``__init__``
    # re-exporting helpers with the same names as the submodules (e.g.
    # ``sector_strength`` function collides with the submodule).
    import importlib
    return {
        "loader":      importlib.import_module("ky_core.scanning.loader"),
        "leaders":     importlib.import_module("ky_core.scanning.leader_scan"),
        "sectors":     importlib.import_module("ky_core.scanning.sector_strength"),
        "breakouts":   importlib.import_module("ky_core.scanning.breakouts"),
        "breadth":     importlib.import_module("ky_core.scanning.breadth"),
        "wizards":     importlib.import_module("ky_core.scanning.wizards"),
        "vcp":         importlib.import_module("ky_core.scanning.vcp"),
        "candlestick": importlib.import_module("ky_core.scanning.candlestick"),
        "divergence":  importlib.import_module("ky_core.scanning.divergence"),
        "ichimoku":    importlib.import_module("ky_core.scanning.ichimoku"),
        "vprofile":    importlib.import_module("ky_core.scanning.vprofile"),
        "support":     importlib.import_module("ky_core.scanning.support"),
        "flow":        importlib.import_module("ky_core.scanning.flow"),
        "themes":      importlib.import_module("ky_core.scanning.themes"),
        "shortint":    importlib.import_module("ky_core.scanning.shortint"),
        "kiwoom":      importlib.import_module("ky_core.scanning.kiwoom_cond"),
    }
