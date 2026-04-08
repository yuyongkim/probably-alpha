from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException

from sepa.api.services import (
    backtest_leaders_payload,
    briefing_latest_payload,
    briefing_payload,
    catalog_payload,
    company_profile_payload,
    dashboard_payload,
    glossary_payload,
    health_payload,
    latest_payload,
    leader_sectors_grouped_payload,
    leader_sectors_payload,
    leader_stocks_payload,
    logic_scoring_payload,
    omega_payload,
    persistence_payload,
    recommendations_history_payload,
    recommendations_latest_payload,
    recommendations_payload,
    sector_members_payload,
    signal_items_payload,
    snapshot_payload,
    stock_analysis_payload,
    stock_overview_payload,
    summary_payload,
    trader_debate_payload,
)


router = APIRouter(tags=['public'])

_SYMBOL_RE = re.compile(r'^[A-Za-z0-9]{1,10}(\.[A-Z]{1,4})?$')
_DATE_RE = re.compile(r'^\d{4}-?\d{2}-?\d{2}$')


def _validate_symbol(symbol: str) -> str:
    s = symbol.strip()
    if not _SYMBOL_RE.match(s):
        raise HTTPException(status_code=400, detail=f'invalid symbol format: {symbol}')
    return s


def _validate_date(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    if not v:
        return None
    if not _DATE_RE.match(v):
        raise HTTPException(status_code=400, detail=f'invalid date format: {value}')
    return v


@router.get('/api/dashboard')
def dashboard(date_dir: str | None = None) -> dict:
    return dashboard_payload(date_dir=date_dir)


@router.get('/api/health')
def health() -> dict:
    return health_payload()


@router.get('/api/latest')
def latest() -> dict:
    return latest_payload()


@router.get('/api/alpha')
def alpha(date_dir: str | None = None) -> dict:
    return signal_items_payload('alpha-passed.json', date_dir=date_dir)


@router.get('/api/beta')
def beta(date_dir: str | None = None) -> dict:
    return signal_items_payload('beta-vcp-candidates.json', date_dir=date_dir)


@router.get('/api/gamma')
def gamma(date_dir: str | None = None) -> dict:
    return signal_items_payload('gamma-insights.json', date_dir=date_dir)


@router.get('/api/delta')
def delta(date_dir: str | None = None) -> dict:
    return signal_items_payload('delta-risk-plan.json', date_dir=date_dir)


@router.get('/api/omega')
def omega(date_dir: str | None = None) -> dict:
    return omega_payload(date_dir=date_dir)


@router.get('/api/summary')
def summary(date_dir: str | None = None) -> dict:
    return summary_payload(date_dir=date_dir)


@router.get('/api/leaders/sectors')
def leader_sectors(date_dir: str | None = None) -> dict:
    return leader_sectors_payload(date_dir=date_dir)


@router.get('/api/leaders/stocks')
def leader_stocks(date_dir: str | None = None) -> dict:
    return leader_stocks_payload(date_dir=date_dir)


@router.get('/api/leaders/sectors-grouped')
def leader_sectors_grouped(date_dir: str | None = None) -> dict:
    return leader_sectors_grouped_payload(date_dir=date_dir)


@router.get('/api/trader-debate')
def trader_debate(date_dir: str | None = None) -> dict:
    return trader_debate_payload(date_dir=date_dir)


@router.get('/api/stock/{symbol}/profile')
def stock_profile(symbol: str, as_of_date: str | None = None) -> dict:
    return company_profile_payload(symbol=_validate_symbol(symbol), as_of_date=_validate_date(as_of_date))


@router.get('/api/stock/{symbol}/analysis')
def stock_analysis(symbol: str, as_of_date: str | None = None) -> dict:
    result = stock_analysis_payload(symbol=_validate_symbol(symbol), as_of_date=_validate_date(as_of_date))
    if result.get('error') == 'no_price_data':
        raise HTTPException(status_code=404, detail=f'no price data for symbol: {symbol}')
    return result


@router.get('/api/stock/{symbol}/overview')
def stock_overview(symbol: str, date_dir: str | None = None, as_of_date: str | None = None, detail: bool = False) -> dict:
    return stock_overview_payload(symbol=_validate_symbol(symbol), date_dir=_validate_date(date_dir), as_of_date=_validate_date(as_of_date), detail=detail)


@router.get('/api/recommendations')
def recommendations(date_dir: str | None = None) -> dict:
    return recommendations_payload(date_dir=date_dir)


@router.get('/api/briefing')
def briefing(date_dir: str | None = None) -> dict:
    return briefing_payload(date_dir=date_dir)


@router.get('/api/recommendations/latest')
def recommendations_latest() -> dict:
    return recommendations_latest_payload()


@router.get('/api/recommendations/history')
def recommendations_history(date_from: str | None = None, date_to: str | None = None, limit: int = 60) -> dict:
    return recommendations_history_payload(date_from=date_from, date_to=date_to, limit=limit)


@router.get('/api/briefing/latest')
def briefing_latest() -> dict:
    return briefing_latest_payload()


@router.get('/api/snapshots/{date_dir}')
def snapshot(date_dir: str) -> dict:
    return snapshot_payload(date_dir)


@router.get('/api/backtest/leaders')
def backtest_leaders(
    period: str = 'weekly',
    date_from: str | None = None,
    date_to: str | None = None,
    buckets: int = 8,
    sector_limit: int = 5,
    stock_limit: int = 10,
) -> dict:
    return backtest_leaders_payload(
        period=period,
        date_from=date_from,
        date_to=date_to,
        buckets=buckets,
        sector_limit=sector_limit,
        stock_limit=stock_limit,
    )


@router.get('/api/glossary')
def glossary() -> dict:
    return glossary_payload()


@router.get('/api/catalog')
def catalog() -> dict:
    return catalog_payload()


@router.get('/api/logic/scoring')
def logic_scoring(date_dir: str | None = None) -> dict:
    return logic_scoring_payload(date_dir=date_dir)


@router.get('/api/sector-members')
def sector_members(sector: str, date_dir: str | None = None) -> dict:
    return sector_members_payload(sector=sector, date_dir=date_dir)


@router.get('/api/stock/{symbol}/quant')
def stock_quant(symbol: str) -> dict:
    """Quantitative metrics computed from Naver financial data."""
    from sepa.scoring.quant_metrics import compute_stock_quant
    return compute_stock_quant(symbol)


@router.get('/api/backtest/presets')
def backtest_presets() -> dict:
    from sepa.backtest.presets import list_presets
    return {'items': list_presets()}


@router.get('/api/screen/multi')
def screen_multi_trader(as_of_date: str | None = None, limit: int = 20) -> dict:
    """Screen stocks against ALL trader presets at once.

    Returns each stock with a list of which presets it passes.
    For the "섹터별 주도주" view showing trader pick badges.
    """
    from sepa.backtest.presets import PRESETS
    from sepa.backtest.screener import screen_universe
    from sepa.data.ohlcv_db import read_ohlcv_batch

    price_data = read_ohlcv_batch(as_of_date=as_of_date, min_rows=200)
    if not price_data:
        return {'items': []}

    # Run each preset and collect which symbols pass
    symbol_presets: dict[str, dict] = {}  # {symbol: {info + presets: [...]}}
    for preset_id, config in PRESETS.items():
        results = screen_universe(config, price_data)
        for r in results[:config.max_positions]:
            sym = r['symbol']
            if sym not in symbol_presets:
                symbol_presets[sym] = {
                    'symbol': sym,
                    'name': r.get('name', sym),
                    'sector': r.get('sector', ''),
                    'close': r.get('close', 0),
                    'tt_passed': r.get('tt_passed', 0),
                    'rs_percentile': r.get('rs_percentile', 0),
                    'score': r.get('score', 0),
                    'presets': [],
                }
            symbol_presets[sym]['presets'].append(preset_id)
            # Keep highest score
            if r.get('score', 0) > symbol_presets[sym]['score']:
                symbol_presets[sym]['score'] = r.get('score', 0)

    # Sort by number of presets matched (more = stronger consensus)
    items = sorted(symbol_presets.values(), key=lambda x: (len(x['presets']), x['score']), reverse=True)
    return {
        'date': as_of_date or 'latest',
        'total_presets': len(PRESETS),
        'items': items[:limit],
    }


@router.get('/api/screen/trader')
def screen_by_trader(
    preset: str = 'minervini',
    as_of_date: str | None = None,
    limit: int = 10,
) -> dict:
    """Screen stocks using a trader preset for a specific date.

    This is NOT a backtest — it answers "what would this trader buy today?"
    """
    from sepa.backtest.presets import get_preset
    from sepa.backtest.screener import screen_universe
    from sepa.data.ohlcv_db import read_ohlcv_batch

    config = get_preset(preset)
    if not config:
        raise HTTPException(status_code=400, detail=f'Unknown preset: {preset}')

    price_data = read_ohlcv_batch(as_of_date=as_of_date, min_rows=200)
    if not price_data:
        return {'preset': preset, 'date': as_of_date, 'items': [], 'error': 'No price data'}

    results = screen_universe(config, price_data)
    return {
        'preset': preset,
        'trader': config.name,
        'description': config.description,
        'date': as_of_date or 'latest',
        'screened_symbols': len(price_data),
        'passed': len(results),
        'items': results[:limit],
    }


@router.get('/api/backtest/run')
def backtest_run(
    start: str = '20251112',
    end: str = '20260402',
    preset: str | None = None,
    initial_cash: float = 100_000_000,
    max_positions: int = 10,
    sector_limit: int = 3,
    top_sectors: int = 5,
    rebalance: str = 'weekly',
    stop_loss_pct: float = 0.075,
    commission: float = 0.00015,
    slippage: float = 0.001,
    tax: float = 0.0018,
    alpha_min_tt: int = 5,
    alpha_rs_threshold: float = 70.0,
    require_ma50: int = 1,
    require_sma200: int = 1,
    sector_filter: int = 1,
    sector_exit: int = 1,
    leader_exit: int = 1,
    require_volume_expansion: int = 0,
    min_volume_ratio: float = 1.5,
    require_near_52w_high: int = 0,
    near_52w_threshold: float = 0.85,
    require_volatility_contraction: int = 0,
    require_20d_breakout: int = 0,
) -> dict:
    from sepa.backtest.engine import BacktestEngine
    from sepa.backtest.presets import get_preset
    from sepa.backtest.report import save_result
    from sepa.backtest.strategy import StrategyConfig

    # Build strategy config (costs flow through config, not class mutation)
    if preset:
        from copy import copy
        base = get_preset(preset)
        if not base:
            return {'error': f'Unknown preset: {preset}'}
        config = copy(base)
        config.initial_cash = int(initial_cash)
        config.max_positions = max_positions
        config.rebalance = rebalance
    else:
        config = StrategyConfig(
            name='Custom',
            initial_cash=int(initial_cash),
            max_positions=max_positions,
            sector_limit=sector_limit,
            top_sectors=top_sectors,
            rebalance=rebalance,
            stop_loss_pct=stop_loss_pct,
            min_tt_pass=alpha_min_tt,
            rs_threshold=alpha_rs_threshold,
            require_ma50=bool(require_ma50),
            require_close_gt_sma200=bool(require_sma200),
            sector_filter=bool(sector_filter),
            sector_exit=bool(sector_exit),
            leader_exit=bool(leader_exit),
            require_volume_expansion=bool(require_volume_expansion),
            min_volume_ratio=min_volume_ratio,
            require_near_52w_high=bool(require_near_52w_high),
            near_52w_threshold=near_52w_threshold,
            require_volatility_contraction=bool(require_volatility_contraction),
            require_20d_breakout=bool(require_20d_breakout),
        )
    config.commission = commission
    config.slippage = slippage
    config.tax = tax

    engine = BacktestEngine(strategy=config)
    result = engine.run(start, end)

    if 'error' not in result:
        save_result(result)
    return result


@router.get('/api/backtest/results')
def backtest_results() -> dict:
    import json
    from pathlib import Path
    out_dir = Path('data/backtest')
    if not out_dir.exists():
        return {'items': []}
    results = []
    for f in sorted(out_dir.glob('bt_*.json'), reverse=True)[:10]:
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            results.append({
                'run_id': data.get('run_id'),
                'strategy': data.get('strategy'),
                'period': data.get('period'),
                'metrics': data.get('metrics'),
            })
        except Exception:
            continue
    return {'items': results}


@router.get('/api/presets/summary')
def presets_summary() -> dict:
    """All 12 presets with latest backtest metrics + today's pick count."""
    import json
    from pathlib import Path
    from sepa.backtest.presets import PRESETS, list_presets

    presets = list_presets()
    bt_dir = Path('data/backtest')

    # Load latest backtest results keyed by strategy name
    bt_cache: dict[str, dict] = {}
    if bt_dir.exists():
        for f in sorted(bt_dir.glob('bt_*.json'), reverse=True):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                name = data.get('strategy', '')
                if name and name not in bt_cache:
                    bt_cache[name] = {
                        'run_id': data.get('run_id'),
                        'period': data.get('period'),
                        'metrics': data.get('metrics'),
                        'equity_curve_length': len(data.get('equity_curve', [])),
                    }
            except Exception:
                continue

    FAMILY_KO = {
        'growth_momentum': '성장 모멘텀',
        'trend_following': '추세추종',
        'swing': '단기 스윙',
        'macro': '매크로 방어',
        'value': '가치투자',
    }

    RISK_LEVEL = {
        'growth_momentum': 'high',
        'trend_following': 'medium',
        'swing': 'high',
        'macro': 'low',
        'value': 'low',
    }

    result = []
    for p in presets:
        config = PRESETS.get(p['id'])
        bt = bt_cache.get(p['name'], {})
        metrics = bt.get('metrics', {})
        result.append({
            **p,
            'family_ko': FAMILY_KO.get(p['family'], p['family']),
            'risk_level': RISK_LEVEL.get(p['family'], 'medium'),
            'backtest': {
                'total_return': metrics.get('total_return'),
                'cagr': metrics.get('cagr'),
                'sharpe': metrics.get('sharpe'),
                'max_drawdown': metrics.get('max_drawdown'),
                'win_rate': metrics.get('trade_win_rate'),
                'total_trades': metrics.get('total_trades'),
                'period': bt.get('period'),
            } if metrics else None,
            'holding_period': '일' if (config and config.rebalance == 'daily') else '주~월',
            'stop_desc': f'{config.stop_loss_pct*100:.0f}% 고정' if config and config.stop_type == 'fixed_pct'
                else f'ATR×{config.atr_stop_multiplier:.0f}' if config and config.stop_type == 'atr_trailing'
                else f'MA{config.ma_exit_period} 이탈' if config and config.stop_type == 'ma_trailing'
                else '-',
        })

    return {'items': result}


@router.get('/api/presets/daily-picks')
def preset_daily_picks(date_dir: str | None = None) -> dict:
    """Pre-computed picks for all presets (from pipeline)."""
    return signal_items_payload('preset-picks.json', date_dir=date_dir, decorate=False)


@router.get('/api/presets/{preset_id}/picks')
def preset_picks(preset_id: str, limit: int = 10, initial_cash: float = 100_000_000) -> dict:
    """Today's picks for a specific preset with execution plan."""
    from sepa.backtest.presets import get_preset
    from sepa.backtest.screener import screen_universe
    from sepa.data.ohlcv_db import read_ohlcv_batch

    config = get_preset(preset_id)
    if not config:
        return {'error': f'Unknown preset: {preset_id}'}

    config.initial_cash = int(initial_cash)
    price_data = read_ohlcv_batch(min_rows=200)
    if not price_data:
        return {'preset': preset_id, 'items': [], 'error': 'No price data'}

    results = screen_universe(config, price_data)
    return {
        'preset': preset_id,
        'strategy': config.name,
        'description': config.description,
        'family': config.family,
        'initial_cash': int(initial_cash),
        'screened': len(price_data),
        'passed': len(results),
        'items': results[:limit],
    }


@router.get('/api/wizards/strategies')
def wizard_strategies() -> dict:
    from sepa.wizards import WizardScreener
    return {'items': WizardScreener.available_strategies(), 'count': len(WizardScreener.available_strategies())}


@router.get('/api/wizards/screen')
def wizard_screen(date_dir: str | None = None) -> dict:
    return signal_items_payload('wizard-screen.json', date_dir=date_dir)


@router.get('/api/persistence')
def persistence(
    kind: str,
    key: str,
    date_to: str | None = None,
    lookback_days: int = 126,
    forward_days: int = 126,
    top_n: int | None = None,
) -> dict:
    return persistence_payload(
        kind=kind,
        key=key,
        date_to=date_to,
        lookback_days=lookback_days,
        forward_days=forward_days,
        top_n=top_n,
    )
