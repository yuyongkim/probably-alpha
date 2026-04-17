from __future__ import annotations

import time
from copy import copy
from datetime import datetime, timedelta

from sepa.backtest.engine import BacktestEngine
from sepa.backtest.presets import get_preset
from sepa.backtest.strategy import StrategyConfig
from sepa.brokers import KisApiError, KisBroker
from sepa.data.etf_universe import get_etf_meta, load_etf_universe
from sepa.data.ohlcv_db import read_ohlcv_batch, upsert_rows
from sepa.data.price_history import normalize_date_token


def etf_universe_payload(*, risk_profile: str | None = None, theme: str | None = None) -> dict:
    items = load_etf_universe()
    normalized_risk = str(risk_profile or '').strip().lower()
    normalized_theme = str(theme or '').strip().lower()

    if normalized_risk:
        items = [item for item in items if str(item.get('risk_profile', '')).strip().lower() == normalized_risk]
    if normalized_theme:
        items = [item for item in items if normalized_theme in str(item.get('theme', '')).strip().lower()]

    return {
        'count': len(items),
        'items': items,
    }


def _parse_token(token: str | None, fallback: datetime) -> datetime:
    normalized = normalize_date_token(token)
    if len(normalized) == 8 and normalized.isdigit():
        return datetime.strptime(normalized, '%Y%m%d')
    return fallback


def _fetch_etf_history_windows(
    broker: KisBroker,
    symbol: str,
    *,
    date_from: str,
    date_to: str,
    sleep_sec: float = 0.35,
    retry_sleep_sec: float = 1.2,
    max_retries_per_window: int = 3,
    max_windows: int = 24,
) -> list[dict]:
    start_dt = datetime.strptime(date_from, '%Y%m%d')
    cursor_end = datetime.strptime(date_to, '%Y%m%d')
    merged: dict[str, dict] = {}
    windows = 0

    while cursor_end >= start_dt and windows < max_windows:
        cursor_start = max(start_dt, cursor_end - timedelta(days=190))
        payload = None
        for attempt in range(1, max_retries_per_window + 1):
            try:
                payload = broker.daily_chart(
                    symbol,
                    date_from=cursor_start.strftime('%Y%m%d'),
                    date_to=cursor_end.strftime('%Y%m%d'),
                )
                break
            except KisApiError as exc:
                message = str(exc)
                is_rate_limited = '초당 거래건수' in message or '잠시 후 다시 시도' in message
                if not is_rate_limited or attempt == max_retries_per_window:
                    raise
                time.sleep(retry_sleep_sec * attempt)
        if payload is None:
            break
        rows = payload.get('rows', [])
        if not rows:
            break

        for row in rows:
            merged[row['date']] = row

        oldest_token = str(rows[0]['date']).replace('-', '')
        oldest_dt = datetime.strptime(oldest_token, '%Y%m%d')
        if oldest_dt <= start_dt:
            break

        next_end = oldest_dt - timedelta(days=1)
        if next_end >= cursor_end:
            break

        cursor_end = next_end
        windows += 1
        time.sleep(sleep_sec)

    return [merged[key] for key in sorted(merged)]


def backfill_etf_history_payload(
    symbols: list[str],
    *,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    broker = KisBroker.from_env()
    if not broker.has_credentials():
        raise KisApiError(503, 'KIS credentials are not configured')

    unique_symbols: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        normalized = str(symbol or '').strip().upper()
        if not normalized or normalized in seen:
            continue
        unique_symbols.append(normalized)
        seen.add(normalized)

    end_dt = _parse_token(date_to, datetime.now())
    start_dt = _parse_token(date_from, end_dt - timedelta(days=900))

    results: list[dict] = []
    for symbol in unique_symbols[:20]:
        history = _fetch_etf_history_windows(
            broker,
            symbol,
            date_from=start_dt.strftime('%Y%m%d'),
            date_to=end_dt.strftime('%Y%m%d'),
        )
        count = upsert_rows(symbol, history)
        meta = get_etf_meta(symbol)
        results.append(
            {
                'symbol': symbol,
                'name': meta.get('name') or symbol,
                'theme': meta.get('theme') or '',
                'rows_written': count,
                'date_from': history[0]['date'] if history else None,
                'date_to': history[-1]['date'] if history else None,
            }
        )

    BacktestEngine.clear_cache()
    return {
        'count': len(results),
        'items': results,
        'requested_date_from': start_dt.strftime('%Y%m%d'),
        'requested_date_to': end_dt.strftime('%Y%m%d'),
    }


def run_etf_backtest_payload(
    symbols: list[str],
    *,
    start: str,
    end: str,
    preset: str | None = None,
    initial_cash: float = 100_000_000,
    max_positions: int = 5,
    rebalance: str = 'weekly',
    stop_loss_pct: float = 0.075,
    commission: float = 0.00015,
    slippage: float = 0.001,
    tax: float = 0.0018,
    benchmark_symbol: str | None = None,
) -> dict:
    normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols if str(symbol).strip())
    if not normalized_symbols:
        return {'error': 'No ETF symbols provided'}

    history = read_ohlcv_batch(list(normalized_symbols), min_rows=200)
    available_symbols = tuple(symbol for symbol in normalized_symbols if symbol in history)
    missing_symbols = [symbol for symbol in normalized_symbols if symbol not in history]
    if not available_symbols:
        return {'error': 'No ETF history found in ohlcv.db', 'missing_symbols': list(normalized_symbols)}

    if preset:
        base = get_preset(preset)
        if not base:
            return {'error': f'Unknown preset: {preset}'}
        config = copy(base)
        config.initial_cash = int(initial_cash)
        config.max_positions = min(max_positions, len(available_symbols))
        config.rebalance = rebalance
        config.stop_loss_pct = stop_loss_pct
    else:
        config = StrategyConfig(
            name='ETF Trend',
            description='ETF whitelist trend backtest',
            family='etf',
            signal_type='trend_template',
            min_tt_pass=4,
            rs_threshold=45.0,
            require_ma50=True,
            require_close_gt_sma200=False,
            initial_cash=int(initial_cash),
            max_positions=min(max_positions, len(available_symbols)),
            rebalance=rebalance,
            stop_loss_pct=stop_loss_pct,
        )

    config.commission = commission
    config.slippage = slippage
    config.tax = tax
    config.symbol_whitelist = available_symbols
    config.ignore_sector_constraints = True
    config.universe_label = 'ETF'
    config.sector_filter = False
    config.sector_limit = 0
    config.top_sectors = max(1, len(available_symbols))
    config.benchmark_symbol = str(benchmark_symbol or get_etf_meta(available_symbols[0]).get('benchmark_symbol') or '').strip().upper()

    engine = BacktestEngine(strategy=config)
    result = engine.run(start, end)
    if isinstance(result, dict):
        result['available_symbols'] = list(available_symbols)
        result['missing_symbols'] = missing_symbols
    return result
