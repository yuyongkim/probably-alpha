from __future__ import annotations

import json
from pathlib import Path
from statistics import mean as _mean

from sepa.analysis.stock_analysis import (
    detect_cup_with_handle as _detect_cwh_fn,
    eps_quality as _eps_quality_fn,
    least_resistance as _least_resistance_fn,
    macd as _macd_fn,
    moving_average as _moving_average_fn,
    trend_template_snapshot as _trend_template_snapshot_fn,
    volume_signal_payload as _volume_signal_payload_fn,
    _round_or_none,
)
from sepa.data.company_facts import estimated_market_cap, read_business_summary
from sepa.data.fundamentals import read_eps_series
from sepa.data.price_history import normalize_date_token, read_price_series
from sepa.data.quantdb import read_company_snapshot, read_financial_summary
from sepa.data.sector_map import get_sector, load_sector_map
from sepa.data.universe import get_symbol_name

from sepa.api.services import (
    decorate_payload,
    resolve_dir,
    session_change_snapshot,
    _read_json_safe,
)


def _build_lightweight_analysis(
    symbol: str,
    price_series: list[dict],
    eps_rows: list[dict],
    alpha_row: dict | None,
    sector_leader_row: dict | None,
) -> dict:
    """Fast single-stock technical analysis that avoids cross-symbol iteration.

    Instead of calling ``build_stock_analysis`` (which invokes ``_ret120_percentile_map``
    and ``sector_breakout_payload`` -- both O(N-symbols) -- we:
    * compute per-stock indicators directly (MA, MACD, least_resistance, etc.)
    * pull RS-percentile from the already-generated alpha-passed.json row
    * pull sector breakout state from the already-generated leader-sectors.json row
    * call ``estimated_market_cap`` (single-stock, fast)
    """

    closes = [row.get('close', 0.0) for row in price_series]
    volumes = [row.get('volume', 0.0) for row in price_series]

    # ---- moving averages (single stock, fast) ----
    ma_map = {
        'sma20': _moving_average_fn(closes, 20),
        'sma50': _moving_average_fn(closes, 50),
        'sma60': _moving_average_fn(closes, 60),
        'sma150': _moving_average_fn(closes, 150),
        'sma200': _moving_average_fn(closes, 200),
        'volume_ma20': _moving_average_fn(volumes, 20),
    }

    # ---- MACD (single stock) ----
    macd_payload = _macd_fn(closes, fast=20, slow=60, signal_window=9)

    # ---- least resistance (single stock) ----
    lr = _least_resistance_fn(price_series)

    # ---- EPS quality (single stock) ----
    epsq = _eps_quality_fn(eps_rows)

    # ---- trend template (single stock) ----
    template = _trend_template_snapshot_fn(price_series, ma_map, macd_payload)

    # ---- volume signal (single stock) ----
    vol_signal = _volume_signal_payload_fn(price_series, ma_map['volume_ma20'])

    # ---- RS percentile from alpha-passed.json (pre-computed, O(1)) ----
    rs_percentile = None
    if alpha_row is not None:
        raw = alpha_row.get('rs_percentile')
        if raw is not None:
            rs_percentile = _round_or_none(float(raw), digits=2)

    # ---- RS state: compute from price series vs benchmark without full map ----
    # We only need the scalar summary fields, not the full line arrays.
    # We skip the expensive per-symbol RS line computation and just reuse
    # the percentile from the JSON plus a lightweight above/below-MA20 check.
    rs_closes = [float(row.get('close', 0.0) or 0.0) for row in price_series]
    rs_state = 'unknown'
    rs_latest = None
    rs_ma20 = None
    rs_high120 = None
    rs_dist = None
    if len(rs_closes) >= 120:
        # simple RS proxy: stock base-100 (no benchmark needed for state heuristic)
        base = rs_closes[-120]
        if base > 0:
            rs_raw = [(c / base) * 100.0 for c in rs_closes[-120:]]
            rs_latest = _round_or_none(rs_raw[-1], digits=2)
            rs_high120 = _round_or_none(max(rs_raw), digits=2)
            rs_ma20_vals = rs_raw[-20:]
            rs_ma20 = _round_or_none(_mean(rs_ma20_vals), digits=2) if len(rs_ma20_vals) == 20 else None
            if rs_latest is not None and rs_high120:
                rs_dist = _round_or_none(((rs_latest / rs_high120) - 1.0) * 100.0, digits=2)
            if rs_latest and rs_ma20 and rs_high120:
                if rs_latest >= rs_high120 * 0.995 and rs_latest >= rs_ma20:
                    rs_state = 'rs_new_high'
                elif rs_latest >= rs_ma20:
                    rs_state = 'rs_above_ma20'
                else:
                    rs_state = 'rs_below_ma20'

    # ---- sector breakout from leader-sectors.json (pre-computed, O(1)) ----
    sector_breakout_state = None
    sector_latest_rs = None
    sector_vol_participation = None
    sector_member_count = None
    if sector_leader_row:
        sector_breakout_state = sector_leader_row.get('breakout_state')
        sector_latest_rs = sector_leader_row.get('latest_rs')
        sector_vol_participation = sector_leader_row.get('volume_participation_ratio')
        sector_member_count = sector_leader_row.get('member_count') or sector_leader_row.get('members')

    # ---- company facts (single stock, fast) ----
    close_price = template.get('close')
    cf_raw = estimated_market_cap(symbol, close_price)
    company_facts = {
        'shares_outstanding': cf_raw.get('shares_outstanding'),
        'last_price_latest': _round_or_none(cf_raw.get('last_price_latest'), digits=2),
        'market_cap_latest': _round_or_none(cf_raw.get('market_cap_latest'), digits=0),
        'market_cap_estimated': _round_or_none(cf_raw.get('market_cap_estimated'), digits=0),
        'market_cap_basis': cf_raw.get('market_cap_basis'),
        'currency': cf_raw.get('currency') or 'KRW',
    }

    as_of_date = price_series[-1]['date'] if price_series else None

    technical_summary = {
        'as_of_date': as_of_date,
        'trend_template': {
            'close': template.get('close'),
            'sma20': template.get('sma20'),
            'sma50': template.get('sma50'),
            'sma150': template.get('sma150'),
            'sma200': template.get('sma200'),
            'high52': template.get('high52'),
            'low52': template.get('low52'),
            'distance_to_high52_pct': template.get('distance_to_high52_pct'),
            'distance_from_low52_pct': template.get('distance_from_low52_pct'),
            'checks': template.get('checks', {}),
            'passed_count': template.get('passed_count', 0),
            'volume_dryup_ratio': template.get('volume_dryup_ratio'),
            'current_volume_ratio_to_avg20': template.get('current_volume_ratio_to_avg20'),
            'tightness_ratio_20_60': template.get('tightness_ratio_20_60'),
            'macd_state': template.get('macd_state'),
        },
        'least_resistance': lr,
        'relative_strength': {
            'benchmark_label': None,
            'rs_percentile_120': rs_percentile,
            'latest': rs_latest,
            'ma20': rs_ma20,
            'high120': rs_high120,
            'distance_to_high120_pct': rs_dist,
            'state': rs_state,
        },
        'volume_signal': {
            'latest_ratio_20': vol_signal.get('latest_ratio_20'),
            'avg_ratio_20': vol_signal.get('avg_ratio_20'),
            'expansion_days_20': vol_signal.get('expansion_days_20'),
            'dryup_days_20': vol_signal.get('dryup_days_20'),
            'state': vol_signal.get('state'),
        },
        'eps_quality': epsq,
        'company_facts': company_facts,
        'cup_with_handle': _detect_cwh_fn(price_series),
    }

    sector_extra = {
        'breakout_state': sector_breakout_state,
        'latest_rs': sector_latest_rs,
        'volume_participation_ratio': sector_vol_participation,
        'member_count': sector_member_count,
    }

    return {'technical_summary': technical_summary, 'sector_extra': sector_extra}


def stock_overview_payload(symbol: str, date_dir: str | None = None, as_of_date: str | None = None, *, detail: bool = False) -> dict:
    """종합 종목 개요.

    detail=False (기본): 프로필 + JSON 기반 파이프라인 스코어 + 실행계획 + 추천 (<1초)
    detail=True: 위 + 기술분석(RS/볼륨/최소저항선) + persistence (수십 초, 캐시 없을 때)
    """
    resolved = resolve_dir(date_dir)
    date_key = resolved.name
    token = normalize_date_token(as_of_date) or date_key

    # --- 회사 프로필 (빠름: 캐시/파일) ---
    snapshot = read_company_snapshot(symbol) or {}
    eps_rows = read_eps_series(symbol, as_of_date=token)
    recent_eps = eps_rows[-8:] if eps_rows else []

    series = read_price_series(symbol, as_of_date=token)
    sparkline: list[float] = []
    latest_price: float | None = snapshot.get('price')
    if series:
        sparkline = [round(float(row.get('close', 0.0)), 2) for row in series[-120:] if row.get('close', 0.0) > 0]
        if sparkline:
            latest_price = sparkline[-1]

    shares = snapshot.get('shares_outstanding')
    mkt_cap_raw = snapshot.get('mkt_cap')
    # QuantDB stores mkt_cap in 억원 (100M KRW). Convert to KRW.
    mkt_cap = mkt_cap_raw * 100_000_000 if mkt_cap_raw else None
    if latest_price and shares and latest_price > 0 and shares > 0:
        mkt_cap = latest_price * shares

    sector_name = get_sector(symbol, load_sector_map())
    business_summary = read_business_summary(symbol)
    profile = {
        'symbol': symbol,
        'name': snapshot.get('name') or get_symbol_name(symbol),
        'market': snapshot.get('market', ''),
        'sector_large': snapshot.get('sector_large', ''),
        'sector_small': snapshot.get('sector_small', ''),
        'sector': sector_name,
        'price': latest_price,
        'mkt_cap': mkt_cap,
        'shares_outstanding': shares,
        'major_holder_ratio': snapshot.get('major_holder_ratio'),
        'business_summary': business_summary,
        'financials': {
            'per': snapshot.get('per'),
            'pbr': snapshot.get('pbr'),
            'roe': snapshot.get('roe'),
            'roa': snapshot.get('roa'),
            'opm': snapshot.get('opm'),
            'dividend_yield': snapshot.get('dividend_yield'),
            'debt_ratio': snapshot.get('debt_ratio'),
            'ev_ebitda': snapshot.get('ev_ebitda'),
            'foreign_1m': snapshot.get('foreign_1m'),
            'return_1m': snapshot.get('return_1m'),
            'return_3m': snapshot.get('return_3m'),
            'f_score': snapshot.get('f_score'),
        },
    }

    # --- 파이프라인 스코어 (빠름: JSON 파일 읽기) ---
    alpha_data = _read_json_safe(resolved / 'alpha-passed.json', [])
    beta_data = _read_json_safe(resolved / 'beta-vcp-candidates.json', [])
    gamma_data = _read_json_safe(resolved / 'gamma-insights.json', {})
    rec_data = _read_json_safe(resolved / 'recommendations.json', [])
    leader_stocks_data = _read_json_safe(resolved / 'leader-stocks.json', [])
    leader_sectors_data = _read_json_safe(resolved / 'leader-sectors.json', [])

    alpha_row = next((r for r in alpha_data if r.get('symbol') == symbol), None)
    beta_row = next((r for r in beta_data if r.get('symbol') == symbol), None)
    gamma_general = gamma_data.get('general', []) if isinstance(gamma_data, dict) else []
    gamma_row = next((r for r in gamma_general if r.get('symbol') == symbol), None)
    rec_row = next((r for r in rec_data if r.get('symbol') == symbol), None)
    leader_stock_row = next((r for r in leader_stocks_data if r.get('symbol') == symbol), None)

    pipeline_scores = {
        'alpha': {
            'passed': alpha_row is not None,
            'score': round(float(alpha_row.get('score', 0.0)), 2) if alpha_row else None,
            'rs_percentile': round(float(alpha_row.get('rs_percentile', 0.0)), 2) if alpha_row else None,
            'checks': alpha_row.get('checks') if alpha_row else None,
        },
        'beta': {
            'passed': beta_row is not None,
            'confidence': round(float(beta_row.get('confidence', 0.0)), 2) if beta_row else None,
            'contraction_ratio': beta_row.get('contraction_ratio') if beta_row else None,
            'volume_dryup': beta_row.get('volume_dryup') if beta_row else None,
            'waves': beta_row.get('waves') if beta_row else None,
        },
        'gamma': {
            'passed': gamma_row is not None,
            'gamma_score': round(float(gamma_row.get('gamma_score', 0.0)), 2) if gamma_row else None,
            'fundamental_score': gamma_row.get('fundamental_score') if gamma_row else None,
            'growth_hint': gamma_row.get('growth_hint') if gamma_row else None,
            'eps_status': gamma_row.get('eps_status') if gamma_row else None,
            'eps_yoy': gamma_row.get('eps_yoy') if gamma_row else None,
            'eps_acceleration': gamma_row.get('eps_acceleration') if gamma_row else None,
            'chem_bonus': gamma_row.get('chem_bonus') if gamma_row else None,
        },
        'leader': {
            'ranked': leader_stock_row is not None,
            'leader_stock_score': leader_stock_row.get('leader_stock_score') if leader_stock_row else None,
            'stock_bucket': leader_stock_row.get('stock_bucket') if leader_stock_row else None,
            'sector_leadership_ready': leader_stock_row.get('sector_leadership_ready') if leader_stock_row else None,
        },
    }

    # --- 섹터 컨텍스트 (JSON 기반, 빠름) ---
    sector_leader_row = next((r for r in leader_sectors_data if r.get('sector') == sector_name), None)
    sector_context = {
        'sector': sector_name,
        'leadership': {
            'leader_score': sector_leader_row.get('leader_score') if sector_leader_row else None,
            'leadership_ready': sector_leader_row.get('leadership_ready') if sector_leader_row else None,
            'sector_bucket': sector_leader_row.get('sector_bucket') if sector_leader_row else None,
            'alpha_ratio': sector_leader_row.get('alpha_ratio') if sector_leader_row else None,
            'beta_ratio': sector_leader_row.get('beta_ratio') if sector_leader_row else None,
            'breakout_state': sector_leader_row.get('breakout_state') if sector_leader_row else None,
            'distance_to_high120_pct': sector_leader_row.get('distance_to_high120_pct') if sector_leader_row else None,
        } if sector_leader_row else None,
    }

    # --- 실행 계획 (JSON 기반 또는 가벼운 계산) ---
    delta_data = _read_json_safe(resolved / 'delta-risk-plan.json', [])
    delta_row = next((r for r in delta_data if r.get('symbol') == symbol), None)

    if delta_row and delta_row.get('entry') is not None:
        execution_plan = {
            'entry': delta_row.get('entry'),
            'stop': delta_row.get('stop'),
            'target': delta_row.get('target'),
            'qty': delta_row.get('qty'),
            'rr_ratio': delta_row.get('rr_ratio'),
            'source': 'delta',
        }
    elif rec_row and rec_row.get('risk_plan', {}).get('entry') is not None:
        rp = rec_row['risk_plan']
        execution_plan = {
            'entry': rp.get('entry'),
            'stop': rp.get('stop'),
            'target': rp.get('target'),
            'qty': rp.get('qty'),
            'rr_ratio': rp.get('rr_ratio'),
            'source': 'recommendation',
        }
    else:
        execution_plan = _compute_execution_plan_light(series, symbol)

    # --- 추천 상태 ---
    recommendation = None
    if rec_row:
        recommendation = {
            'recommendation_score': rec_row.get('recommendation_score'),
            'conviction': rec_row.get('conviction'),
            'why': rec_row.get('why'),
            'risk_plan': rec_row.get('risk_plan'),
        }

    # --- 세션 변동 ---
    session = session_change_snapshot(symbol, date_key)

    result: dict = {
        'date_dir': date_key,
        'profile': profile,
        'session': session,
        'pipeline_scores': pipeline_scores,
        'sector_context': sector_context,
        'execution_plan': execution_plan,
        'recommendation': recommendation,
        'eps_recent': recent_eps,
        'sparkline': sparkline,
        'financial_summary': read_financial_summary(symbol),
        'technical_summary': None,
        'persistence': None,
    }

    # --- detail=True: lightweight 기술분석 (단일 종목만) + persistence (30일) ---
    if detail:
        lw = _build_lightweight_analysis(
            symbol=symbol,
            price_series=series,
            eps_rows=eps_rows,
            alpha_row=alpha_row,
            sector_leader_row=sector_leader_row,
        )
        result['technical_summary'] = lw['technical_summary']
        se = lw['sector_extra']
        result['sector_context']['breakout_state'] = se.get('breakout_state')
        result['sector_context']['latest_rs'] = se.get('latest_rs')
        result['sector_context']['volume_participation_ratio'] = se.get('volume_participation_ratio')
        result['sector_context']['member_count'] = se.get('member_count')

        # Persistence is intentionally skipped here — it requires scanning
        # hundreds of JSON snapshots (37s+).  The frontend already has
        # /api/persistence?kind=stock&key=… for on-demand loading.

    return result


def _compute_execution_plan_light(series: list[dict], symbol: str) -> dict | None:
    """JSON에 없을 때 가격 시리즈만으로 간단한 실행계획 생성 (build_stock_analysis 호출 안 함)."""
    if not series:
        return None
    closes = [float(row.get('close', 0.0)) for row in series if row.get('close')]
    if not closes:
        return None

    last = closes[-1]
    stop_pct = 0.075
    target_r = 2.0
    risk_budget = 200000.0

    entry = round(last * 1.005, 2)
    stop = round(entry * (1.0 - stop_pct), 2)
    risk = max(0.01, entry - stop)
    target = round(entry + risk * target_r, 2)
    rr = round((target - entry) / risk, 2)
    qty = max(1, int(risk_budget // risk))

    return {'entry': entry, 'stop': stop, 'target': target, 'qty': qty, 'rr_ratio': rr, 'source': 'light'}
