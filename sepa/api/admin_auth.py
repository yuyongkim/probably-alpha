from __future__ import annotations

import logging
import secrets
from typing import Iterable

from fastapi import HTTPException, Request

from config.settings import load_settings

logger = logging.getLogger(__name__)

_AUTH_HEADER = {'WWW-Authenticate': 'Bearer realm="sepa-admin"'}
_LEGACY_HEADER = 'x-sepa-admin-token'


def load_admin_tokens() -> tuple[str, ...]:
    return load_settings().admin_tokens


def _matches_any_token(provided: str, tokens: Iterable[str]) -> bool:
    matched = False
    for token in tokens:
        if secrets.compare_digest(provided, token):
            matched = True
    return matched


def _extract_token(
    request: Request,
    allow_legacy_header: bool,
) -> tuple[str, str]:
    auth_header = request.headers.get('authorization', '').strip()
    if auth_header:
        scheme, _, token = auth_header.partition(' ')
        if scheme.lower() != 'bearer' or not token.strip():
            return '', 'malformed_authorization'
        return token.strip(), 'authorization'

    if allow_legacy_header:
        legacy = request.headers.get(_LEGACY_HEADER, '').strip()
        if legacy:
            return legacy, 'legacy_header'
    return '', 'missing'


def verify_admin_token(
    request: Request,
) -> None:
    current_settings = load_settings()
    tokens = current_settings.admin_tokens
    if not tokens:
        raise HTTPException(
            status_code=503,
            detail='admin authentication unavailable',
            headers=_AUTH_HEADER,
        )

    provided, source = _extract_token(request, current_settings.admin_allow_legacy_header)
    if provided and _matches_any_token(provided, tokens):
        return

    if current_settings.admin_audit_failures:
        logger.warning(
            'admin auth failed method=%s path=%s source=%s client=%s user_agent=%s',
            request.method,
            request.url.path,
            source,
            request.client.host if request.client else 'unknown',
            request.headers.get('user-agent', '-')[:160],
        )
    raise HTTPException(
        status_code=401,
        detail='admin authentication failed',
        headers=_AUTH_HEADER,
    )
