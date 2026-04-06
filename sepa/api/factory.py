from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import Settings, settings
from sepa.api.routes_admin import router as admin_router
from sepa.api.routes_public import router as public_router
from sepa.api.services import APP_NAME

logger = logging.getLogger(__name__)


def _warmup_caches() -> None:
    """Pre-warm expensive LRU caches in a background thread so the first
    user request doesn't pay the cold-start cost (~60 s)."""
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

        # Also discover the latest signal directory date (may differ from price date)
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

        # Pre-warm stock overview for pipeline-selected symbols
        logger.info('cache warmup: stock overviews ...')
        from sepa.api.services_stock_overview import warmup_overview_cache
        n = warmup_overview_cache()
        logger.info('cache warmup: %d stock overviews cached', n)
    except Exception:
        logger.exception('cache warmup failed (non-fatal)')


def build_cors_middleware_options(current_settings: Settings = settings) -> dict:
    origins = list(current_settings.cors_origins)
    allow_credentials = bool(current_settings.cors_allow_credentials)
    if '*' in origins and allow_credentials:
        allow_credentials = False

    return {
        'allow_origins': origins,
        'allow_credentials': allow_credentials,
        'allow_methods': ['*'],
        'allow_headers': ['*'],
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start cache warmup in background thread so server accepts requests immediately
    thread = threading.Thread(target=_warmup_caches, daemon=True, name='cache-warmup')
    thread.start()
    yield


def create_app(current_settings: Settings = settings) -> FastAPI:
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title=APP_NAME, version='0.2.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, **build_cors_middleware_options(current_settings))
    app.include_router(public_router)
    app.include_router(admin_router)

    # Serve frontend static files at root (so single port works for tunnel)
    frontend_dir = Path('sepa/frontend')
    if frontend_dir.exists():
        app.mount('/', StaticFiles(directory=str(frontend_dir), html=True), name='frontend')

    return app
