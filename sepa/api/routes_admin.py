from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sepa.api.admin_auth import verify_admin_token
from sepa.api.models import (
    DailySignalsBuildRequest,
    EtfBacktestRunRequest,
    EtfHistoryBackfillRequest,
    HistoryBackfillRequest,
    KisCashOrderRequest,
    KisOrderPreviewRequest,
)
from sepa.api.routes_public import run_backtest_job
from sepa.api.services import backfill_history_payload, build_daily_signals
from sepa.api.services_etf import backfill_etf_history_payload, run_etf_backtest_payload
from sepa.api.services_kis import kis_order_cash_payload, kis_order_preview_payload
from sepa.brokers import KisApiError

router = APIRouter(prefix='/api/admin', tags=['admin'], dependencies=[Depends(verify_admin_token)])


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


@router.post('/backtest/run')
def admin_backtest_run(
    start: str = Query('20251112', pattern=r'^\d{8}$'),
    end: str = Query('20260402', pattern=r'^\d{8}$'),
    preset: str | None = None,
    initial_cash: float = Query(100_000_000, ge=1_000_000, le=10_000_000_000),
    max_positions: int = Query(10, ge=1, le=50),
    sector_limit: int = Query(3, ge=1, le=20),
    top_sectors: int = Query(5, ge=1, le=20),
    rebalance: str = Query('weekly', pattern=r'^(daily|weekly|biweekly|monthly)$'),
    stop_loss_pct: float = Query(0.075, ge=0.0, le=0.5),
    commission: float = Query(0.00015, ge=0.0, le=0.01),
    slippage: float = Query(0.001, ge=0.0, le=0.05),
    tax: float = Query(0.0018, ge=0.0, le=0.05),
    alpha_min_tt: int = Query(5, ge=0, le=8),
    alpha_rs_threshold: float = Query(70.0, ge=0.0, le=100.0),
    require_ma50: int = Query(1, ge=0, le=1),
    require_sma200: int = Query(1, ge=0, le=1),
    sector_filter: int = Query(1, ge=0, le=1),
    sector_exit: int = Query(1, ge=0, le=1),
    leader_exit: int = Query(1, ge=0, le=1),
    require_volume_expansion: int = Query(0, ge=0, le=1),
    min_volume_ratio: float = Query(1.5, ge=0.0, le=10.0),
    require_near_52w_high: int = Query(0, ge=0, le=1),
    near_52w_threshold: float = Query(0.85, ge=0.0, le=1.0),
    require_volatility_contraction: int = Query(0, ge=0, le=1),
    require_20d_breakout: int = Query(0, ge=0, le=1),
) -> dict:
    return run_backtest_job(
        start=start,
        end=end,
        preset=preset,
        initial_cash=initial_cash,
        max_positions=max_positions,
        sector_limit=sector_limit,
        top_sectors=top_sectors,
        rebalance=rebalance,
        stop_loss_pct=stop_loss_pct,
        commission=commission,
        slippage=slippage,
        tax=tax,
        alpha_min_tt=alpha_min_tt,
        alpha_rs_threshold=alpha_rs_threshold,
        require_ma50=require_ma50,
        require_sma200=require_sma200,
        sector_filter=sector_filter,
        sector_exit=sector_exit,
        leader_exit=leader_exit,
        require_volume_expansion=require_volume_expansion,
        min_volume_ratio=min_volume_ratio,
        require_near_52w_high=require_near_52w_high,
        near_52w_threshold=near_52w_threshold,
        require_volatility_contraction=require_volatility_contraction,
        require_20d_breakout=require_20d_breakout,
    )


@router.post('/kis/order-preview')
def admin_kis_order_preview(request: KisOrderPreviewRequest) -> dict:
    try:
        return kis_order_preview_payload(
            request.symbol,
            order_price=request.order_price,
            order_type=request.order_type,
            include_cma=request.include_cma,
            include_overseas=request.include_overseas,
        )
    except KisApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post('/kis/order-cash')
def admin_kis_order_cash(request: KisCashOrderRequest) -> dict:
    try:
        return kis_order_cash_payload(
            request.symbol,
            side=request.side,
            quantity=request.quantity,
            order_price=request.order_price,
            order_type=request.order_type,
            exchange_code=request.exchange_code,
            sell_type=request.sell_type,
            condition_price=request.condition_price,
        )
    except KisApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post('/kis/etf-history/backfill')
def admin_kis_etf_history_backfill(request: EtfHistoryBackfillRequest) -> dict:
    try:
        return backfill_etf_history_payload(
            symbols=request.symbols,
            date_from=request.date_from,
            date_to=request.date_to,
        )
    except KisApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post('/backtest/etf/run')
def admin_backtest_etf_run(request: EtfBacktestRunRequest) -> dict:
    return run_etf_backtest_payload(
        symbols=request.symbols,
        start=request.start,
        end=request.end,
        preset=request.preset,
        initial_cash=request.initial_cash,
        max_positions=request.max_positions,
        rebalance=request.rebalance,
        stop_loss_pct=request.stop_loss_pct,
        commission=request.commission,
        slippage=request.slippage,
        tax=request.tax,
        benchmark_symbol=request.benchmark_symbol,
    )
