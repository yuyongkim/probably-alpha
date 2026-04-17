from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitPolicy:
    api_rpm: int = 120
    static_rpm: int = 300
    window_seconds: int = 60
    trust_proxy_headers: bool = False
    trusted_proxy_ips: tuple[str, ...] = ()


def _normalize_ip(value: str) -> str:
    return value.strip()


def resolve_client_ip(request: Request, policy: RateLimitPolicy) -> str:
    direct_ip = _normalize_ip(request.client.host) if request.client and request.client.host else 'unknown'
    if not policy.trust_proxy_headers or not direct_ip or direct_ip == 'unknown':
        return direct_ip
    if policy.trusted_proxy_ips and direct_ip not in policy.trusted_proxy_ips:
        return direct_ip

    forwarded_for = request.headers.get('x-forwarded-for', '')
    if forwarded_for:
        parts = [_normalize_ip(part) for part in forwarded_for.split(',') if part.strip()]
        if parts:
            return parts[0]

    real_ip = _normalize_ip(request.headers.get('x-real-ip', ''))
    if real_ip:
        return real_ip
    return direct_ip


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Configurable in-memory rate limiter with proxy-aware client resolution."""

    def __init__(self, app, policy: RateLimitPolicy):
        super().__init__(app)
        self.policy = policy
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _window(self, key: str) -> deque[float]:
        return self._hits[key]

    def _limit_for_path(self, path: str) -> tuple[str, int]:
        if path.startswith('/api/'):
            return 'api', self.policy.api_rpm
        return 'static', self.policy.static_rpm

    def _check_rate(self, key: str, limit: int) -> tuple[bool, int]:
        now = time.time()
        window_start = now - float(self.policy.window_seconds)
        with self._lock:
            hits = self._window(key)
            while hits and hits[0] <= window_start:
                hits.popleft()
            remaining = max(limit - len(hits), 0)
            if remaining <= 0:
                return False, 0
            hits.append(now)
            return True, max(limit - len(hits), 0)

    async def dispatch(self, request: Request, call_next):
        if request.method == 'OPTIONS':
            return await call_next(request)

        bucket, limit = self._limit_for_path(request.url.path)
        client_ip = resolve_client_ip(request, self.policy)
        key = f'{bucket}:{client_ip}'
        allowed, remaining = self._check_rate(key, limit)
        headers = {
            'X-RateLimit-Limit': str(limit),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(self.policy.window_seconds),
        }

        if not allowed:
            logger.warning(
                'rate limit exceeded for %s bucket=%s method=%s path=%s',
                client_ip,
                bucket,
                request.method,
                request.url.path,
            )
            return Response(
                content='{"error":"rate_limit_exceeded","message":"Too many requests"}',
                status_code=429,
                media_type='application/json',
                headers={**headers, 'Retry-After': str(self.policy.window_seconds)},
            )

        response = await call_next(request)
        response.headers.update(headers)
        return response
