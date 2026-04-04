from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, '').strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name, '').strip().lower()
    if not raw:
        return default
    return raw in {'1', 'true', 'yes', 'on'}


def _csv_env(name: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    raw = os.getenv(name, '').strip()
    if not raw:
        return default
    return tuple(item.strip() for item in raw.split(',') if item.strip())


def _default_cors_origins() -> tuple[str, ...]:
    frontend_port = _int_env('FRONTEND_PORT', 8080)
    frontend_host = os.getenv('FRONTEND_HOST', '127.0.0.1').strip() or '127.0.0.1'
    origins: list[str] = []
    hosts = ['127.0.0.1', 'localhost'] if frontend_host in {'0.0.0.0', '127.0.0.1'} else [frontend_host]
    for host in hosts:
        origins.append(f'http://{host}:{frontend_port}')
    # Always include the default dev frontend port (8080) if env overrides to a different port
    if frontend_port != 8080:
        for host in hosts:
            origins.append(f'http://{host}:8080')
    return tuple(dict.fromkeys(origins))


@dataclass(frozen=True)
class Settings:
    dart_api_key: str = os.getenv("DART_API_KEY", "")
    kiwoom_app_key: str = os.getenv("KIWOOM_APP_KEY", "")
    kiwoom_secret_key: str = os.getenv("KIWOOM_SECRET_KEY", "")
    kiwoom_market_type: str = os.getenv("KIWOOM_MARKET_TYPE", "KOSPI")
    kiwoom_query_date: str = os.getenv("KIWOOM_QUERY_DATE", "")
    kiwoom_token_url: str = os.getenv("KIWOOM_TOKEN_URL", "")
    kiwoom_ohlcv_url: str = os.getenv("KIWOOM_OHLCV_URL", "")

    ecos_api_key: str = os.getenv("ECOS_API_KEY", "")
    fred_api_key: str = os.getenv("FRED_API_KEY", "")
    eia_api_key: str = os.getenv("EIA_API_KEY", "")

    api_host: str = os.getenv("API_HOST", "127.0.0.1")
    api_port: int = _int_env("API_PORT", 8000)
    frontend_host: str = os.getenv("FRONTEND_HOST", "127.0.0.1")
    frontend_port: int = _int_env("FRONTEND_PORT", 8080)

    cors_origins: tuple[str, ...] = field(default_factory=lambda: _csv_env("SEPA_CORS_ORIGINS", _default_cors_origins()))
    cors_allow_credentials: bool = _bool_env("SEPA_CORS_ALLOW_CREDENTIALS", False)

    data_root: Path = Path(os.getenv("SEPA_DATA_ROOT", "data/market-data"))
    signal_root: Path = Path(os.getenv("SEPA_SIGNAL_ROOT", "data/daily-signals"))
    audit_root: Path = Path(os.getenv("SEPA_AUDIT_ROOT", "data/audit-logs"))
    db_path: Path = Path(os.getenv("SEPA_DB_PATH", "data/sepa.db"))
    cache_root: Path = Path(os.getenv("SEPA_CACHE_ROOT", "data/cache"))


settings = Settings()
