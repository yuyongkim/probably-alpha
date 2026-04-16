from __future__ import annotations

import logging
import time
import threading
from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import Settings, settings
from sepa.api.routes_admin import router as admin_router
from sepa.api.routes_public import router as public_router
from sepa.api.services import APP_NAME

logger = logging.getLogger(__name__)


# ── Security Headers Middleware ──────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: blob:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Prevent MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # XSS protection (legacy browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # HSTS (force HTTPS)
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions policy (disable unnecessary browser features)
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=()'
        )

        return response


# ── Rate Limiting Middleware ─────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter per IP.

    Limits:
      - API endpoints: 60 requests per minute
      - Static files: 200 requests per minute
    """

    def __init__(self, app, api_rpm: int = 60, static_rpm: int = 200):
        super().__init__(app)
        self.api_rpm = api_rpm
        self.static_rpm = static_rpm
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _check_rate(self, key: str, limit: int) -> bool:
        now = time.time()
        window = 60.0
        with self._lock:
            hits = self._hits[key]
            # Remove old entries
            self._hits[key] = [t for t in hits if now - t < window]
            if len(self._hits[key]) >= limit:
                return False
            self._hits[key].append(now)
            return True

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else 'unknown'
        path = request.url.path

        if path.startswith('/api/'):
            key = f'api:{client_ip}'
            limit = self.api_rpm
        else:
            key = f'static:{client_ip}'
            limit = self.static_rpm

        if not self._check_rate(key, limit):
            return Response(
                content='{"error":"rate_limit_exceeded","message":"Too many requests"}',
                status_code=429,
                media_type='application/json',
                headers={'Retry-After': '60'},
            )

        return await call_next(request)


# ── Error Sanitization ──────────────────────────────────────────────────

class ErrorSanitizeMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return sanitized error response."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception('Unhandled error on %s %s', request.method, request.url.path)
            return Response(
                content='{"error":"internal_error","message":"An internal error occurred"}',
                status_code=500,
                media_type='application/json',
            )


# ── Cache Warmup ────────────────────────────────────────────────────────

def _warmup_caches() -> None:
    """Pre-warm expensive LRU caches in a background thread."""
    try:
        from sepa.data.price_history import available_dates
        from sepa.analysis.stock_analysis import (
            _ret120_percentile_map,
            _market_proxy_series,
            sector_breakout_payload,
        )
        from sepa.data.universe import load_symbols
        from sepa.data.sector_map import load_sector_map, get_sector

        logger.info('cache warmup: available_dates ...')
        dates = available_dates()
        latest_date = dates[-1] if dates else None

        from config.settings import settings as _settings
        signal_dirs = sorted(p.name for p in _settings.signal_root.glob('*') if p.is_dir())
        warmup_dates = {d for d in {latest_date, signal_dirs[-1] if signal_dirs else None} if d}

        logger.info('cache warmup: _ret120_percentile_map (dates: %s) ...', warmup_dates)
        _ret120_percentile_map(as_of_date=None)
        for d in warmup_dates:
            _ret120_percentile_map(as_of_date=d)

        logger.info('cache warmup: _market_proxy_series ...')
        _market_proxy_series(as_of_date=None)
        for d in warmup_dates:
            _market_proxy_series(as_of_date=d)

        logger.info('cache warmup: market index ...')
        from sepa.data.market_index import read_market_index_series
        for market in ('KOSPI', 'KOSDAQ'):
            read_market_index_series(market, as_of_date=None)
            for d in warmup_dates:
                read_market_index_series(market, as_of_date=d)

        logger.info('cache warmup: sector_breakout_payload ...')
        sector_map = load_sector_map()
        sectors_seen: set[str] = set()
        for symbol in load_symbols():
            sector = get_sector(symbol, sector_map)
            if sector and sector not in sectors_seen:
                sectors_seen.add(sector)
                sector_breakout_payload(sector, as_of_date=None)
                for d in warmup_dates:
                    sector_breakout_payload(sector, as_of_date=d)

        logger.info('cache warmup: done (%d sectors cached)', len(sectors_seen))

        logger.info('cache warmup: stock overviews ...')
        from sepa.api.services_stock_overview import warmup_overview_cache
        n = warmup_overview_cache()
        logger.info('cache warmup: %d stock overviews cached', n)
    except Exception:
        logger.exception('cache warmup failed (non-fatal)')


# ── CORS Configuration ──────────────────────────────────────────────────

def build_cors_middleware_options(current_settings: Settings = settings) -> dict:
    # Restrict CORS to specific origins (not wildcard)
    origins = list(current_settings.cors_origins)
    if '*' in origins:
        # Replace wildcard with specific allowed origins
        origins = [
            'https://sepa.yule.pics',
            'http://localhost:8200',
            'http://127.0.0.1:8200',
            'http://localhost:8280',
            'http://127.0.0.1:8280',
        ]

    return {
        'allow_origins': origins,
        'allow_credentials': False,
        'allow_methods': ['GET', 'POST'],  # Only what we need
        'allow_headers': ['Content-Type', 'Authorization'],
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=_warmup_caches, daemon=True, name='cache-warmup')
    thread.start()
    yield


def create_app(current_settings: Settings = settings) -> FastAPI:
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(
        title=APP_NAME,
        version='0.2.0',
        lifespan=lifespan,
        # Don't expose docs in production
        docs_url=None if current_settings.api_host != '127.0.0.1' else '/docs',
        redoc_url=None,
    )

    # Middleware order matters: outermost first
    app.add_middleware(ErrorSanitizeMiddleware)
    app.add_middleware(RateLimitMiddleware, api_rpm=120, static_rpm=300)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CORSMiddleware, **build_cors_middleware_options(current_settings))

    app.include_router(public_router)
    app.include_router(admin_router)

    # Serve frontend
    frontend_dir = Path('sepa/frontend')
    if frontend_dir.exists():
        app.mount('/', StaticFiles(directory=str(frontend_dir), html=True), name='frontend')

    return app
