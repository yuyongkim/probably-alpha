from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from fastapi import HTTPException

from config.settings import settings
from sepa.analysis.persistence import build_persistence
from sepa.analysis.sector_logic import build_logic_payload, build_sector_members
from sepa.analysis.stock_analysis import build_stock_analysis
from sepa.data.company_facts import read_business_summary
from sepa.data.glossary import glossary_terms
from sepa.data.price_history import (
    available_dates,
    leading_available_dates,
    nearest_available_date,
    normalize_date_token,
    read_price_series,
    trailing_available_dates,
)
from sepa.data.fundamentals import read_eps_series
from sepa.data.quantdb import read_company_snapshot
from sepa.data.universe import get_symbol_name, load_universe
from sepa.pipeline.backfill_history import backfill_history
from sepa.pipeline.run_after_close import build_after_close
from sepa.storage.recommendation_store import get_history, get_latest, get_leader_buckets, get_snapshot, get_snapshot_bounds


APP_NAME = 'SEPA API'
SIGNALS_ROOT = settings.signal_root
SIGNAL_GENERATION_HINT = (
    'Generate the missing signal bundle via POST /api/admin/daily-signals '
    'or run `python -m sepa.pipeline.run_after_close`.'
)


def resolve_dir(date_dir: str | None = None) -> Path:
    token = normalize_date_token(date_dir)
    if token:
        dates = available_dates()
        if not dates:
            raise HTTPException(status_code=404, detail='no market dates available')
        direct_path = SIGNALS_ROOT / token
        if token < dates[0]:
            raise HTTPException(status_code=404, detail=f'date out of supported range: {token}')
        if token > dates[-1]:
            if direct_path.exists():
                return direct_path
            raise HTTPException(status_code=404, detail=f'date out of supported range: {token}')
        resolved = nearest_available_date(token)
        path = direct_path if direct_path.exists() else (SIGNALS_ROOT / resolved)
        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail=f'signal bundle not found for {resolved}. {SIGNAL_GENERATION_HINT}',
            )
        return path

    dirs = sorted(path for path in SIGNALS_ROOT.glob('*') if path.is_dir())
    if not dirs:
        raise HTTPException(status_code=404, detail='no daily signals found')
    return dirs[-1]


def resolve_backfill_window(
    date_to: str | None,
    lookback_days: int,
    forward_days: int,
    *,
    explicit_date_from: str | None = None,
) -> tuple[str, str, str]:
    resolved = nearest_available_date(normalize_date_token(date_to) or None)
    if not resolved:
        raise HTTPException(status_code=404, detail='no market dates available')

    if explicit_date_from:
        date_from = normalize_date_token(explicit_date_from)
        if not date_from:
            raise HTTPException(status_code=400, detail='invalid date_from')
    else:
        trailing = trailing_available_dates(resolved, length=max(1, min(lookback_days, 1260)))
        date_from = trailing[0] if trailing else resolved

    forward = leading_available_dates(resolved, length=max(1, min(forward_days, 1260)))
    date_until = forward[-1] if forward else resolved
    return resolved, date_from, date_until


def read_json(path: Path):
    if not path.exists():
        raise HTTPException(status_code=404, detail=f'missing file: {path.name}')
    return json.loads(path.read_text(encoding='utf-8'))


def decorate_payload(payload):
    if isinstance(payload, list):
        return [decorate_payload(item) for item in payload]
    if isinstance(payload, dict):
        out = {key: decorate_payload(value) for key, value in payload.items()}
        symbol = str(out.get('symbol', '') or '').strip()
        if symbol and not out.get('name'):
            out['name'] = get_symbol_name(symbol)
        return out
    return payload


@lru_cache(maxsize=512)
def session_change_snapshot(symbol: str, date_to: str) -> dict:
    token = normalize_date_token(date_to)
    if not symbol or not token:
        return {}

    series = read_price_series(symbol, as_of_date=token)
    if not series:
        return {}

    current = series[-1]
    previous = series[-2] if len(series) >= 2 else None
    close = float(current.get('close', 0.0) or 0.0)
    prev_close = float(previous.get('close', 0.0) or 0.0) if previous else 0.0
    change_abs = (close - prev_close) if prev_close > 0 else None
    change_pct = ((close / prev_close) - 1.0) * 100.0 if prev_close > 0 else None

    return {
        'date': current.get('date'),
        'previous_date': previous.get('date') if previous else None,
        'close': round(close, 2) if close > 0 else None,
        'prev_close': round(prev_close, 2) if prev_close > 0 else None,
        'change_abs': round(change_abs, 2) if change_abs is not None else None,
        'change_pct': round(change_pct, 2) if change_pct is not None else None,
    }


def decorate_backtest_items(items: list[dict]) -> list[dict]:
    decorated: list[dict] = []
    for bucket in items or []:
        date_to = normalize_date_token(bucket.get('date_to'))
        stocks = []
        for item in bucket.get('stocks', []) or []:
            enriched = dict(item)
            enriched['session'] = dict(session_change_snapshot(str(item.get('symbol', '') or ''), date_to))
            stocks.append(enriched)
        decorated.append({**bucket, 'stocks': stocks})
    return decorated


def health_payload() -> dict:
    return {
        'status': 'ok',
        'service': APP_NAME,
        'time': datetime.now().isoformat(timespec='seconds'),
    }


def build_daily_signals(date_dir: str | None = None, *, refresh_live: bool = False) -> dict:
    resolved = build_after_close(as_of_date=normalize_date_token(date_dir) or None, refresh_live=refresh_live)
    return {
        'status': 'ok',
        'date_dir': resolved,
        'refresh_live': refresh_live,
    }


def backfill_history_payload(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    lookback_days: int = 126,
    forward_days: int = 126,
    force: bool = False,
) -> dict:
    resolved, window_from, window_to = resolve_backfill_window(
        date_to=date_to,
        lookback_days=lookback_days,
        forward_days=forward_days,
        explicit_date_from=date_from,
    )
    backfill_history(days=None, date_from=window_from, date_to=window_to, force=force)
    return {
        'status': 'ok',
        'resolved_date': resolved,
        'date_from': window_from,
        'date_to': window_to,
        'force': force,
    }


def latest_payload() -> dict:
    return {'date_dir': resolve_dir().name}


def signal_items_payload(filename: str, *, date_dir: str | None = None, decorate: bool = True) -> dict:
    resolved = resolve_dir(date_dir)
    payload = read_json(resolved / filename)
    items = decorate_payload(payload) if decorate else payload
    return {'date_dir': resolved.name, 'items': items}


def omega_payload(date_dir: str | None = None) -> dict:
    return signal_items_payload('omega-final-picks.json', date_dir=date_dir)


def summary_payload(date_dir: str | None = None) -> dict:
    resolved = resolve_dir(date_dir)
    alpha_items = read_json(resolved / 'alpha-passed.json')
    beta_items = read_json(resolved / 'beta-vcp-candidates.json')
    delta_items = read_json(resolved / 'delta-risk-plan.json')
    omega_items = read_json(resolved / 'omega-final-picks.json')
    stock_items = read_json(resolved / 'leader-stocks.json')
    sector_items = read_json(resolved / 'leader-sectors.json')
    picks = omega_items.get('final_picks', []) if isinstance(omega_items, dict) else []
    confirmed_stocks = [item for item in stock_items if isinstance(item, dict) and item.get('stock_bucket') == 'confirmed_leader']
    setup_candidates = [item for item in stock_items if isinstance(item, dict) and item.get('stock_bucket') == 'setup_candidate']
    confirmed_sectors = [item for item in sector_items if isinstance(item, dict) and item.get('sector_bucket') == 'confirmed_leader']
    sector_watchlist = [item for item in sector_items if isinstance(item, dict) and item.get('sector_bucket') == 'watchlist']
    return {
        'date_dir': resolved.name,
        'counts': {
            'alpha': len(alpha_items) if isinstance(alpha_items, list) else 0,
            'beta': len(beta_items) if isinstance(beta_items, list) else 0,
            'delta': len(delta_items) if isinstance(delta_items, list) else 0,
            'picks': len(picks),
            'leader_stocks': len(confirmed_stocks),
            'setup_candidates': len(setup_candidates),
            'leader_sectors': len(confirmed_sectors),
            'sector_watchlist': len(sector_watchlist),
        },
    }


def leader_sectors_payload(date_dir: str | None = None) -> dict:
    return signal_items_payload('leader-sectors.json', date_dir=date_dir, decorate=False)


def leader_stocks_payload(date_dir: str | None = None) -> dict:
    return signal_items_payload('leader-stocks.json', date_dir=date_dir)


def leader_sectors_grouped_payload(date_dir: str | None = None) -> dict:
    return signal_items_payload('leader-sectors-grouped.json', date_dir=date_dir)


def trader_debate_payload(date_dir: str | None = None) -> dict:
    resolved = resolve_dir(date_dir)
    path = resolved / 'trader-debate.json'
    if not path.exists():
        return {'date_dir': resolved.name, 'items': None, 'available': False}
    data = read_json(path)
    return {'date_dir': resolved.name, 'items': data, 'available': True}


def company_profile_payload(symbol: str, as_of_date: str | None = None) -> dict:
    token = normalize_date_token(as_of_date) or None
    snapshot = read_company_snapshot(symbol) or {}

    # EPS: use fundamentals.read_eps_series (auto-merges CSV + QuantDB)
    eps_rows = read_eps_series(symbol, as_of_date=token)
    recent_eps = eps_rows[-8:] if eps_rows else []

    # Price & sparkline: from OHLCV CSV (always fresh)
    series = read_price_series(symbol, as_of_date=token)
    sparkline: list[float] = []
    latest_price: float | None = snapshot.get('price')
    if series:
        sparkline = [round(float(row.get('close', 0.0)), 2) for row in series[-120:] if row.get('close', 0.0) > 0]
        if sparkline:
            latest_price = sparkline[-1]

    # Market cap: recalculate from latest price if shares are known
    shares = snapshot.get('shares_outstanding')
    mkt_cap_raw = snapshot.get('mkt_cap')
    # QuantDB stores mkt_cap in 억원 (100M KRW). Convert to KRW.
    mkt_cap = mkt_cap_raw * 100_000_000 if mkt_cap_raw else None
    if latest_price and shares and latest_price > 0 and shares > 0:
        mkt_cap = latest_price * shares

    return {
        'symbol': symbol,
        'name': snapshot.get('name') or get_symbol_name(symbol),
        'market': snapshot.get('market', ''),
        'sector_large': snapshot.get('sector_large', ''),
        'sector_small': snapshot.get('sector_small', ''),
        'price': latest_price,
        'mkt_cap': mkt_cap,
        'shares_outstanding': shares,
        'major_holder_ratio': snapshot.get('major_holder_ratio'),
        'business_summary': read_business_summary(symbol),
        'eps_recent': recent_eps,
        'sparkline': sparkline,
    }


def stock_analysis_payload(symbol: str, as_of_date: str | None = None) -> dict:
    return decorate_payload(build_stock_analysis(symbol, as_of_date=normalize_date_token(as_of_date) or None))


def recommendations_payload(date_dir: str | None = None) -> dict:
    return signal_items_payload('recommendations.json', date_dir=date_dir)


def briefing_payload(date_dir: str | None = None) -> dict:
    return signal_items_payload('briefing.json', date_dir=date_dir, decorate=False)


def recommendations_latest_payload() -> dict:
    latest_row = get_latest()
    if not latest_row:
        return recommendations_payload()
    return {'date_dir': latest_row['date_dir'], 'items': decorate_payload(latest_row['recommendations'])}


def recommendations_history_payload(date_from: str | None = None, date_to: str | None = None, limit: int = 60) -> dict:
    items = get_history(
        date_from=normalize_date_token(date_from) or None,
        date_to=normalize_date_token(date_to) or None,
        limit=limit,
    )
    return {'items': decorate_payload(items)}


def briefing_latest_payload() -> dict:
    latest_row = get_latest()
    if not latest_row:
        return briefing_payload()
    return {'date_dir': latest_row['date_dir'], 'items': latest_row.get('briefing', {})}


def snapshot_payload(date_dir: str) -> dict:
    item = get_snapshot(normalize_date_token(date_dir))
    if not item:
        raise HTTPException(status_code=404, detail=f'snapshot not found: {date_dir}')
    return decorate_payload(item)


def backtest_leaders_payload(
    *,
    period: str = 'weekly',
    date_from: str | None = None,
    date_to: str | None = None,
    buckets: int = 8,
    sector_limit: int = 5,
    stock_limit: int = 10,
) -> dict:
    try:
        items = get_leader_buckets(
            period=period,
            date_from=normalize_date_token(date_from) or None,
            date_to=normalize_date_token(date_to) or None,
            bucket_limit=buckets,
            sector_limit=sector_limit,
            stock_limit=stock_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        'period': period,
        'items': decorate_payload(decorate_backtest_items(items)),
    }


def glossary_payload() -> dict:
    return {'items': glossary_terms()}


def catalog_payload() -> dict:
    universe = load_universe()
    sectors = sorted({row.get('sector', 'Other') for row in universe})
    dates = available_dates()
    bounds = get_snapshot_bounds()
    return {
        'universe_count': len(universe),
        'sector_count': len(sectors),
        'sector_names': sectors,
        'available_date_min': dates[0] if dates else None,
        'available_date_max': dates[-1] if dates else None,
        'history_years_supported': round(len(dates) / 252.0, 2) if dates else 0.0,
        'snapshot_date_min': bounds.get('min_date'),
        'snapshot_date_max': bounds.get('max_date'),
        'snapshot_count': bounds.get('count', 0),
    }


def logic_scoring_payload(date_dir: str | None = None) -> dict:
    resolved = resolve_dir(date_dir)
    return build_logic_payload(resolved.name, as_of_date=resolved.name)


def sector_members_payload(sector: str, date_dir: str | None = None) -> dict:
    resolved = resolve_dir(date_dir)
    return decorate_payload(build_sector_members(sector=sector, date_dir=resolved.name, as_of_date=resolved.name))


def persistence_payload(
    *,
    kind: str,
    key: str,
    date_to: str | None = None,
    lookback_days: int = 126,
    forward_days: int = 126,
    top_n: int | None = None,
) -> dict:
    resolved = nearest_available_date(normalize_date_token(date_to) or None)
    return build_persistence(
        kind=kind,
        key=key,
        date_to=resolved,
        lookback_days=max(1, min(lookback_days, 1260)),
        forward_days=max(1, min(forward_days, 1260)),
        top_n=top_n,
    )


def _read_json_safe(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return default


# ---------------------------------------------------------------------------
# Re-exports from split-out modules (backward compatibility)
# ---------------------------------------------------------------------------
from sepa.api.services_dashboard import dashboard_payload  # noqa: E402, F401
from sepa.api.services_stock_overview import (  # noqa: E402, F401
    _build_lightweight_analysis,
    _compute_execution_plan_light,
    stock_overview_payload,
)
