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


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name, '').strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _admin_tokens_from_env() -> tuple[str, ...]:
    tokens: list[str] = []
    primary = os.getenv('SEPA_ADMIN_TOKEN', '').strip()
    previous = _csv_env('SEPA_ADMIN_PREVIOUS_TOKENS', ())
    additional = _csv_env('SEPA_ADMIN_TOKENS', ())
    for token in (primary, *previous, *additional):
        if token and token not in tokens:
            tokens.append(token)
    return tuple(tokens)


def _default_cors_origins() -> tuple[str, ...]:
    api_port = _int_env('API_PORT', 8200)
    frontend_port = _int_env('FRONTEND_PORT', 8280)
    frontend_host = os.getenv('FRONTEND_HOST', '127.0.0.1').strip() or '127.0.0.1'
    origins: list[str] = ['https://sepa.yule.pics']
    hosts = ['127.0.0.1', 'localhost'] if frontend_host in {'0.0.0.0', '127.0.0.1'} else [frontend_host]
    for host in hosts:
        origins.append(f'http://{host}:{api_port}')
        if frontend_port != api_port:
            origins.append(f'http://{host}:{frontend_port}')
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
    api_port: int = _int_env("API_PORT", 8200)
    frontend_host: str = os.getenv("FRONTEND_HOST", "127.0.0.1")
    frontend_port: int = _int_env("FRONTEND_PORT", 8280)
    enable_docs: bool = field(default_factory=lambda: _bool_env("SEPA_ENABLE_DOCS", False))
    admin_tokens: tuple[str, ...] = field(default_factory=_admin_tokens_from_env)
    admin_allow_legacy_header: bool = field(default_factory=lambda: _bool_env("SEPA_ADMIN_ALLOW_LEGACY_HEADER", True))
    admin_audit_failures: bool = field(default_factory=lambda: _bool_env("SEPA_ADMIN_AUDIT_FAILURES", True))
    rate_limit_api_rpm: int = field(default_factory=lambda: _int_env("SEPA_RATE_LIMIT_API_RPM", 120))
    rate_limit_static_rpm: int = field(default_factory=lambda: _int_env("SEPA_RATE_LIMIT_STATIC_RPM", 300))
    rate_limit_window_seconds: int = field(default_factory=lambda: _int_env("SEPA_RATE_LIMIT_WINDOW_SECONDS", 60))
    rate_limit_trust_proxy_headers: bool = field(default_factory=lambda: _bool_env("SEPA_RATE_LIMIT_TRUST_PROXY_HEADERS", False))
    rate_limit_trusted_proxy_ips: tuple[str, ...] = field(
        default_factory=lambda: _csv_env("SEPA_RATE_LIMIT_TRUSTED_PROXY_IPS", ())
    )
    llm_provider: str = os.getenv("SEPA_LLM_PROVIDER", "ollama")
    llm_timeout_seconds: int = _int_env("SEPA_LLM_TIMEOUT_SECONDS", 60)
    llm_temperature: float = _float_env("SEPA_LLM_TEMPERATURE", 0.2)
    llm_max_history_messages: int = _int_env("SEPA_LLM_MAX_HISTORY_MESSAGES", 8)
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("SEPA_OLLAMA_MODEL", "qwen3.5:4b")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("SEPA_GEMINI_MODEL", "gemini-2.5-flash")

    cors_origins: tuple[str, ...] = field(default_factory=lambda: _csv_env("SEPA_CORS_ORIGINS", _default_cors_origins()))
    cors_allow_credentials: bool = _bool_env("SEPA_CORS_ALLOW_CREDENTIALS", False)

    data_root: Path = Path(os.getenv("SEPA_DATA_ROOT", "data/market-data"))
    signal_root: Path = Path(os.getenv("SEPA_SIGNAL_ROOT", "data/daily-signals"))
    audit_root: Path = Path(os.getenv("SEPA_AUDIT_ROOT", "data/audit-logs"))
    db_path: Path = Path(os.getenv("SEPA_DB_PATH", "data/ohlcv.db"))
    cache_root: Path = Path(os.getenv("SEPA_CACHE_ROOT", "data/cache"))


def load_settings() -> Settings:
    return Settings()


settings = load_settings()
