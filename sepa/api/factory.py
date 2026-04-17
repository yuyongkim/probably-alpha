from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import Settings, settings
from sepa.api.csp import build_content_security_policy
from sepa.api.rate_limit import RateLimitMiddleware, RateLimitPolicy
from sepa.api.routes_admin import router as admin_router
from sepa.api.routes_public import router as public_router
from sepa.api.services import APP_NAME

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""

    def __init__(self, app, csp_value: str):
        super().__init__(app)
        self.csp_value = csp_value

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        response.headers['Content-Security-Policy'] = self.csp_value
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=()'
        )
        return response


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


def build_cors_middleware_options(current_settings: Settings = settings) -> dict:
    origins = list(current_settings.cors_origins)
    if '*' in origins:
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
        'allow_methods': ['GET', 'POST'],
        'allow_headers': ['Content-Type', 'Authorization', 'X-SEPA-Admin-Token'],
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=_warmup_caches, daemon=True, name='cache-warmup')
    thread.start()
    yield


def create_app(current_settings: Settings = settings) -> FastAPI:
    from fastapi.staticfiles import StaticFiles

    frontend_dir = Path('sepa/frontend')
    csp_value = build_content_security_policy(frontend_dir) if frontend_dir.exists() else "default-src 'self'"
    rate_limit_policy = RateLimitPolicy(
        api_rpm=current_settings.rate_limit_api_rpm,
        static_rpm=current_settings.rate_limit_static_rpm,
        window_seconds=current_settings.rate_limit_window_seconds,
        trust_proxy_headers=current_settings.rate_limit_trust_proxy_headers,
        trusted_proxy_ips=current_settings.rate_limit_trusted_proxy_ips,
    )

    app = FastAPI(
        title=APP_NAME,
        version='0.2.0',
        lifespan=lifespan,
        docs_url='/docs' if current_settings.enable_docs else None,
        redoc_url=None,
    )

    app.add_middleware(ErrorSanitizeMiddleware)
    app.add_middleware(RateLimitMiddleware, policy=rate_limit_policy)
    app.add_middleware(SecurityHeadersMiddleware, csp_value=csp_value)
    app.add_middleware(CORSMiddleware, **build_cors_middleware_options(current_settings))

    app.include_router(public_router)
    app.include_router(admin_router)

    if frontend_dir.exists():
        app.mount('/', StaticFiles(directory=str(frontend_dir), html=True), name='frontend')

    return app
