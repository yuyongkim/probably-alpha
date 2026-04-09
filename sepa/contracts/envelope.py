"""JSON output envelope — adds schema headers to all pipeline outputs.

Every pipeline output JSON must include these fields per OUTPUT_SCHEMA_SPEC.md:
- schema_version, date, generated_at, pipeline_run_id, stale_data
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime

from sepa.data.price_history import latest_trading_date


def _default_date_dir() -> str:
    return latest_trading_date()


_RUN_ID: str | None = None


def _get_run_id() -> str:
    global _RUN_ID
    if _RUN_ID is None:
        _RUN_ID = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    return _RUN_ID


def reset_run_id() -> None:
    """Reset the run ID (call at the start of each pipeline execution)."""
    global _RUN_ID
    _RUN_ID = None


def wrap_output(
    data,
    *,
    schema_version: str = "1.0",
    date_dir: str | None = None,
    stale_data: bool = False,
) -> dict:
    """Wrap pipeline output data with the standard envelope.

    If *data* is a list, it becomes the value of a ``"items"`` key.
    If *data* is a dict, its keys are merged into the envelope.
    """
    envelope: dict = {
        "schema_version": schema_version,
        "date": date_dir or _default_date_dir(),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "pipeline_run_id": _get_run_id(),
        "stale_data": stale_data,
    }

    if isinstance(data, list):
        envelope["items"] = data
    elif isinstance(data, dict):
        envelope.update(data)
    else:
        envelope["data"] = data

    return envelope


def unwrap_output(data):
    """Unwrap an envelope-wrapped JSON output back to original data.

    If *data* is a dict with ``schema_version`` and ``items``, returns ``items``.
    Otherwise returns data as-is.
    """
    if isinstance(data, dict) and 'schema_version' in data and 'items' in data:
        return data['items']
    return data
