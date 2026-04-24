"""Shared helpers for the value sub-routers."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Optional

# Make packages/core & packages/adapters importable without `pip install -e .`
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
_PKG_ADAPTERS = Path(__file__).resolve().parents[4] / "packages" / "adapters"
for _p in (_PKG_CORE, _PKG_ADAPTERS):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

log = logging.getLogger("routers.value")

DEFAULT_AS_OF = "2026-04-17"


def envelope(
    data: Any = None,
    error: Any = None,
    ok: Optional[bool] = None,
) -> dict[str, Any]:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}
