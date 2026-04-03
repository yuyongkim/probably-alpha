from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sepa.api.models import DailySignalsBuildRequest, HistoryBackfillRequest
from sepa.api.services import backfill_history_payload, build_daily_signals

_bearer = HTTPBearer(auto_error=False)


def _verify_admin_token(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> None:
    token = os.getenv('SEPA_ADMIN_TOKEN', '').strip()
    if not token:
        raise HTTPException(status_code=503, detail='SEPA_ADMIN_TOKEN not configured')
    if credentials is None or credentials.credentials != token:
        raise HTTPException(status_code=401, detail='invalid or missing admin token')


router = APIRouter(prefix='/api/admin', tags=['admin'], dependencies=[Depends(_verify_admin_token)])


@router.post('/daily-signals')
def admin_daily_signals(request: DailySignalsBuildRequest) -> dict:
    return build_daily_signals(request.date_dir, refresh_live=request.refresh_live)


@router.post('/history/backfill')
def admin_history_backfill(request: HistoryBackfillRequest) -> dict:
    return backfill_history_payload(
        date_from=request.date_from,
        date_to=request.date_to,
        lookback_days=request.lookback_days,
        forward_days=request.forward_days,
        force=request.force,
    )
