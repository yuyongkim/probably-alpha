from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from sepa.analysis.stock_analysis import sector_breakout_payload
from sepa.data.scoring_explainer import scoring_reference
from sepa.data.price_history import read_price_series
from sepa.data.universe import get_symbol_name, load_universe


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        # Unwrap envelope
        if isinstance(data, dict) and 'schema_version' in data and 'items' in data:
            return data['items']
        return data
    except json.JSONDecodeError:
        return default


@lru_cache(maxsize=512)
def _ret120_for_symbol(symbol: str, as_of_date: str | None = None) -> float:
    closes = [row.get('close', 0.0) for row in read_price_series(symbol, as_of_date=as_of_date)]
    if len(closes) < 121:
        return 0.0
    base = closes[-121]
    if base <= 0:
        return 0.0
    return float(closes[-1]) / float(base) - 1.0


@lru_cache(maxsize=128)
def build_sector_members(
    sector: str,
    date_dir: str,
    as_of_date: str | None = None,
    signal_root: Path = Path('data/daily-signals'),
) -> dict:
    day_dir = signal_root / date_dir
    alpha = _read_json(day_dir / 'alpha-passed.json', [])
    beta = _read_json(day_dir / 'beta-vcp-candidates.json', [])
    gamma = _read_json(day_dir / 'gamma-insights.json', {})
    recs = _read_json(day_dir / 'recommendations.json', [])
    leader_sectors = _read_json(day_dir / 'leader-sectors.json', [])
    sector_summary = next((item for item in leader_sectors if item.get('sector') == sector), None)

    alpha_map = {item.get('symbol'): item for item in alpha}
    beta_map = {item.get('symbol'): item for item in beta}
    gamma_map = {item.get('symbol'): item for item in (gamma.get('general', []) if isinstance(gamma, dict) else [])}
    rec_map = {item.get('symbol'): item for item in recs}
    sector_score = float((sector_summary or {}).get('leader_score', 0.0))
    sector_ready = bool((sector_summary or {}).get('leadership_ready', False))
    sector_bucket = str((sector_summary or {}).get('sector_bucket') or ('confirmed_leader' if sector_ready else 'watchlist'))

    members = []
    for row in load_universe():
        symbol = row['symbol']
        if str(row.get('sector', '') or '') != sector:
            continue
        alpha_score = float(alpha_map.get(symbol, {}).get('score', 0.0))
        beta_confidence = float(beta_map.get(symbol, {}).get('confidence', 0.0))
        gamma_score = float(gamma_map.get(symbol, {}).get('gamma_score', 0.0))
        ret120_value = _ret120_for_symbol(symbol, as_of_date=as_of_date)
        leader_stock_score = (
            alpha_score * 0.43
            + beta_confidence * 4.0
            + gamma_score * 3.0
            + ret120_value * 100.0 * 0.10
            + sector_score * 0.25
        )
        recommendation = rec_map.get(symbol, {})
        members.append(
            {
                'symbol': symbol,
                'name': get_symbol_name(symbol),
                'sector': sector,
                'sector_bucket': sector_bucket,
                'sector_leadership_ready': sector_ready,
                'stock_bucket': 'confirmed_leader' if sector_ready else 'setup_candidate',
                'alpha_pass': symbol in alpha_map,
                'beta_pass': symbol in beta_map,
                'recommended': symbol in rec_map,
                'alpha_score': round(alpha_score, 2),
                'beta_confidence': round(beta_confidence, 2),
                'gamma_score': round(gamma_score, 2),
                'ret120': round(ret120_value, 4),
                'ret120_pct': round(ret120_value * 100.0, 2),
                'leader_stock_score': round(leader_stock_score, 2),
                'recommendation_score': recommendation.get('recommendation_score'),
                'conviction': recommendation.get('conviction'),
            }
        )

    members.sort(
        key=lambda item: (
            item['recommended'],
            item['sector_leadership_ready'],
            item['leader_stock_score'],
            item['alpha_score'],
        ),
        reverse=True,
    )
    sector_analysis = sector_breakout_payload(sector, as_of_date=as_of_date)
    return {
        'date_dir': date_dir,
        'sector': sector,
        'sector_summary': sector_summary or {'sector': sector},
        'sector_analysis': sector_analysis,
        'members': members,
    }


@lru_cache(maxsize=128)
def build_logic_payload(date_dir: str, as_of_date: str | None = None) -> dict:
    day_dir = Path('data/daily-signals') / date_dir
    sectors = _read_json(day_dir / 'leader-sectors.json', [])
    stocks = _read_json(day_dir / 'leader-stocks.json', [])
    recommendations = _read_json(day_dir / 'recommendations.json', [])

    top_sector = sectors[0] if sectors else {}
    top_stock = stocks[0] if stocks else {}
    top_recommendation = recommendations[0] if recommendations else {}

    examples = []
    if top_sector:
        examples.append(
            {
                'title': f"{top_sector.get('sector')} sector score example",
                'expression': (
                    f"((0.32 x {top_sector.get('sector_rs_percentile', 0) / 100:.4f}) "
                    f"+ (0.24 x {top_sector.get('alpha_ratio', 0):.4f}) "
                    f"+ (0.14 x {top_sector.get('beta_ratio', 0):.4f}) "
                    f"+ (0.18 x {top_sector.get('breakout_proximity_score', 0):.4f}) "
                    f"+ (0.12 x {top_sector.get('volume_participation_ratio', 0):.4f})) "
                    f"x breadth {top_sector.get('breadth_multiplier', 0):.4f} x 100 = {top_sector.get('leader_score')}"
                ),
                'meaning': 'Sector RS, breadth, setup proximity, and participation must align before a sector is treated as leadership.',
            }
        )
    if top_stock:
        examples.append(
            {
                'title': f"{top_stock.get('name')} leader-stock score example",
                'expression': (
                    f"(0.43 x {top_stock.get('alpha_score', 0)}) "
                    f"+ (4.0 x {top_stock.get('beta_confidence', 0)}) "
                    f"+ (3.0 x {top_stock.get('gamma_score', 0)}) "
                    f"+ (0.10 x {top_stock.get('ret120_pct', 0)}) "
                    f"+ (0.25 x {top_stock.get('sector_leader_score', 0)}) = {top_stock.get('leader_stock_score')}"
                ),
                'meaning': 'A stock can rank only if the underlying sector is also acting like leadership or at least a credible setup.',
            }
        )
    if top_recommendation:
        why = top_recommendation.get('why', {})
        examples.append(
            {
                'title': f"{top_recommendation.get('name', top_recommendation.get('symbol'))} recommendation score example",
                'expression': (
                    f"(0.45 x {why.get('alpha_score', 0)}) "
                    f"+ (0.20 x ({why.get('beta_confidence', 0)} x 10)) "
                    f"+ (0.20 x ({why.get('gamma_score', 0)} x 10)) "
                    f"+ (0.10 x {why.get('ret120_pct', 0)}) "
                    f"+ (0.05 x least_resistance_bonus) = {top_recommendation.get('recommendation_score')}"
                ),
                'meaning': 'Recommendation ranking still applies EPS and least-resistance gates after leader selection.',
            }
        )

    return {
        **scoring_reference(),
        'date_dir': date_dir,
        'examples': examples,
    }
