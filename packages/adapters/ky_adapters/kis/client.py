"""KIS adapter skeleton.

This module provides the shape the rest of ky-platform expects, but performs
**no real network calls** until ``KIS_APP_KEY`` / ``KIS_APP_SECRET`` are
provisioned. Downstream code must call :meth:`KISAdapter.healthcheck` and
branch on ``ok=False`` rather than assuming quotes are available.

Per policy (2026-04-22) KIS is the sole backbone for quotes / universe /
orders. Kiwoom / Yahoo / Naver adapters are deliberately not being created.
"""
from __future__ import annotations

from typing import Any

from ky_adapters.base import BaseAdapter, HealthStatus


class KISAdapter(BaseAdapter):
    source_id = "kis"
    priority = 1  # P0 — single backbone when configured

    def __init__(
        self,
        *,
        app_key: str | None = None,
        app_secret: str | None = None,
        base_url: str | None = None,
        env: str | None = None,
    ) -> None:
        super().__init__()
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url or "https://openapi.koreainvestment.com:9443"
        self.env = env or "prod"

    @classmethod
    def from_settings(cls) -> "KISAdapter":
        return cls(
            app_key=cls._env("KIS_APP_KEY"),
            app_secret=cls._env("KIS_APP_SECRET"),
            base_url=cls._env("KIS_BASE_URL"),
            env=cls._env("KIS_ENV"),
        )

    # --------- Contract ---------

    def healthcheck(self) -> dict[str, Any]:
        if not self.app_key or not self.app_secret:
            return HealthStatus(
                ok=False,
                source_id=self.source_id,
                last_error="KIS_APP_KEY/KIS_APP_SECRET not configured",
                extra={"message": "not implemented — provision KIS credentials to enable"},
            ).to_dict()
        # Even with keys present, we do not issue real calls in this skeleton.
        return HealthStatus(
            ok=False,
            source_id=self.source_id,
            last_error="skeleton — real calls disabled",
            extra={"message": "KISAdapter is currently a no-op scaffold"},
        ).to_dict()

    # --------- Future API surface (intentionally unimplemented) ---------

    def get_quote(self, symbol: str) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError("KISAdapter.get_quote is not implemented yet")

    def get_universe(self, market: str = "KRX") -> list[dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError("KISAdapter.get_universe is not implemented yet")
