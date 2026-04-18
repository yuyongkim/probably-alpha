from __future__ import annotations

from typing import Any, Literal

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


class EtfProfileRecommendationRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=20)
    risk_profile: Literal['conservative', 'balanced', 'aggressive'] = 'balanced'
    date_from: str | None = None
    date_to: str | None = None


class KisOrderPreviewRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    order_price: float = Field(gt=0)
    order_type: str = Field(default='00', min_length=2, max_length=2)
    include_cma: Literal['Y', 'N'] = 'N'
    include_overseas: Literal['Y', 'N'] = 'N'


class KisCashOrderRequest(BaseModel):
    side: Literal['buy', 'sell']
    symbol: str = Field(min_length=1, max_length=12)
    quantity: int = Field(ge=1, le=1_000_000)
    order_price: float = Field(ge=0)
    order_type: str = Field(default='00', min_length=2, max_length=2)
    exchange_code: str = Field(default='KRX', min_length=3, max_length=3)
    sell_type: str = ''
    condition_price: str = ''


class EtfHistoryBackfillRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=20)
    date_from: str | None = None
    date_to: str | None = None


class EtfBacktestRunRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=20)
    start: str = Field(pattern=r'^\d{8}$')
    end: str = Field(pattern=r'^\d{8}$')
    preset: str | None = None
    initial_cash: float = Field(default=100_000_000, ge=1_000_000, le=10_000_000_000)
    max_positions: int = Field(default=5, ge=1, le=20)
    rebalance: Literal['daily', 'weekly', 'biweekly', 'monthly'] = 'weekly'
    stop_loss_pct: float = Field(default=0.075, ge=0.0, le=0.5)
    commission: float = Field(default=0.00015, ge=0.0, le=0.01)
    slippage: float = Field(default=0.001, ge=0.0, le=0.05)
    tax: float = Field(default=0.0018, ge=0.0, le=0.05)
    benchmark_symbol: str | None = None


class AssistantChatMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=4000)


class AssistantChatRequest(BaseModel):
    page_id: str = Field(min_length=1, max_length=64)
    messages: list[AssistantChatMessage] = Field(min_length=1, max_length=12)
    context: Any | None = None
