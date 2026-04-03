from __future__ import annotations

from fastapi import HTTPException

from sepa.analysis.sector_logic import build_logic_payload
from sepa.data.price_history import available_dates
from sepa.data.universe import load_universe
from sepa.storage.recommendation_store import get_history, get_latest, get_snapshot_bounds

from sepa.api.services import decorate_payload, read_json, resolve_dir


def dashboard_payload(date_dir: str | None = None) -> dict:
    """Combined endpoint: resolves date once and reads each JSON file once."""
    resolved = resolve_dir(date_dir)
    date_key = resolved.name

    # Read each JSON file exactly once
    alpha_items = read_json(resolved / 'alpha-passed.json')
    beta_items = read_json(resolved / 'beta-vcp-candidates.json')
    delta_items = read_json(resolved / 'delta-risk-plan.json')
    omega_items = read_json(resolved / 'omega-final-picks.json')
    stock_items = read_json(resolved / 'leader-stocks.json')
    sector_items = read_json(resolved / 'leader-sectors.json')
    rec_items = read_json(resolved / 'recommendations.json')

    try:
        briefing_items = read_json(resolved / 'briefing.json')
    except HTTPException:
        briefing_items = {}

    try:
        grouped_items = read_json(resolved / 'leader-sectors-grouped.json')
    except HTTPException:
        grouped_items = []

    # summary counts (reuse already-loaded data)
    picks = omega_items.get('final_picks', []) if isinstance(omega_items, dict) else []
    confirmed_stocks = [i for i in stock_items if isinstance(i, dict) and i.get('stock_bucket') == 'confirmed_leader']
    setup_candidates = [i for i in stock_items if isinstance(i, dict) and i.get('stock_bucket') == 'setup_candidate']
    confirmed_sectors = [i for i in sector_items if isinstance(i, dict) and i.get('sector_bucket') == 'confirmed_leader']
    sector_watchlist = [i for i in sector_items if isinstance(i, dict) and i.get('sector_bucket') == 'watchlist']

    summary = {
        'date_dir': date_key,
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

    # briefing (latest from DB or file)
    latest_row = get_latest()
    if latest_row:
        briefing = {'date_dir': latest_row['date_dir'], 'items': latest_row.get('briefing', {})}
    else:
        briefing = {'date_dir': date_key, 'items': briefing_items}

    # recommendations (latest from DB or file)
    if latest_row:
        recommendations = {'date_dir': latest_row['date_dir'], 'items': decorate_payload(latest_row['recommendations'])}
    else:
        recommendations = {'date_dir': date_key, 'items': decorate_payload(rec_items)}

    # history
    history_items = get_history(date_from=None, date_to=None, limit=30)

    # logic
    logic = build_logic_payload(date_key, as_of_date=date_key)

    # catalog
    universe = load_universe()
    sectors = sorted({row.get('sector', 'Other') for row in universe})
    dates = available_dates()
    bounds = get_snapshot_bounds()
    catalog = {
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

    return {
        'summary': summary,
        'briefing': briefing,
        'sectors': {'date_dir': date_key, 'items': sector_items},
        'stocks': {'date_dir': date_key, 'items': decorate_payload(stock_items)},
        'recommendations': recommendations,
        'omega': {'date_dir': date_key, 'items': omega_items},
        'history': {'items': decorate_payload(history_items)},
        'logic': logic,
        'catalog': catalog,
        'sectors_grouped': {'items': grouped_items if isinstance(grouped_items, list) else []},
    }
