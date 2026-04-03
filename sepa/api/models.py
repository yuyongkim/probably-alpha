from __future__ import annotations

from pydantic import BaseModel, Field


class DailySignalsBuildRequest(BaseModel):
    date_dir: str | None = None
    refresh_live: bool = False


class HistoryBackfillRequest(BaseModel):
    date_from: str | None = None
    date_to: str | None = None
    lookback_days: int = Field(default=126, ge=1, le=1260)
    forward_days: int = Field(default=126, ge=1, le=1260)
    force: bool = False
