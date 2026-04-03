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
