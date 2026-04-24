"""Shared helpers for quant sub-routers."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Make packages/core importable without requiring `pip install -e .`.
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

log = logging.getLogger("routers.quant")

DEFAULT_AS_OF = "2026-04-17"


def envelope(data: Any = None, error: Any = None, ok: Optional[bool] = None) -> Dict[str, Any]:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}


def markets(markets_csv: str) -> tuple[str, ...]:
    allowed = {"KOSPI", "KOSDAQ", "KONEX"}
    picks = tuple(m.strip().upper() for m in markets_csv.split(",") if m.strip())
    picks = tuple(m for m in picks if m in allowed)
    return picks or ("KOSPI", "KOSDAQ")
