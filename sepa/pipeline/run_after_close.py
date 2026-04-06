from __future__ import annotations

import json
import logging
from datetime import datetime
from html import escape
from pathlib import Path

from sepa.agents.leaders import MinerviniLeaders
from sepa.agents.recommender import MinerviniRecommender
from sepa.contracts.envelope import wrap_output
from sepa.data.price_history import format_date_token, normalize_date_token
from sepa.pipeline.run_live_cycle import main as run_live_cycle
from sepa.pipeline.run_mvp import run_pipeline
from sepa.pipeline.wizard_screen import run_wizard_screen
from sepa.reporting.briefing import build_briefing
from sepa.storage.recommendation_store import upsert_daily

logger = logging.getLogger(__name__)


LATEST_PATH = Path('data/daily-signals/latest.json')


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def write_report(path: Path, date_dir: str, sectors: list[dict], stocks: list[dict], recs: list[dict]) -> None:
    lines = [
        '# Daily Minervini Leaders Report',
        '',
        f'- Date: {format_date_token(date_dir)}',
        '',
        '## Leading Sectors',
    ]
    for index, item in enumerate(sectors, start=1):
        lines.append(
            f"{index}. {item['sector']} | score={item['leader_score']} | "
            f"alpha={item['alpha_count']} beta={item['beta_count']}"
        )

    lines += ['', '## Leading Stocks']
    for index, item in enumerate(stocks, start=1):
        lines.append(
            f"{index}. {item['symbol']} ({item['sector']}) | leader_score={item['leader_stock_score']} | "
            f"A={item['alpha_score']} B={item['beta_confidence']} G={item['gamma_score']}"
        )

    lines += ['', '## Recommended Picks']
    for index, item in enumerate(recs, start=1):
        risk_plan = item.get('risk_plan', {})
        lines.append(
            f"{index}. {item['symbol']} [{item['conviction']}] score={item['recommendation_score']} | "
            f"entry={risk_plan.get('entry')} stop={risk_plan.get('stop')} "
            f"target={risk_plan.get('target')} rr={risk_plan.get('rr_ratio')}"
        )

    path.write_text('\n'.join(lines), encoding='utf-8')


def write_html_report(path: Path, date_dir: str, recs: list[dict]) -> None:
    rows = []
    for index, item in enumerate(recs, start=1):
        risk_plan = item.get('risk_plan', {})
        why = item.get('why', {})
        rows.append(
            f"<tr><td>{index}</td><td>{escape(str(item['symbol']))}</td><td>{escape(str(item.get('sector','-')))}</td>"
            f"<td>{escape(str(item.get('conviction','-')))}</td><td>{escape(str(item.get('recommendation_score','-')))}</td>"
            f"<td>{escape(str(why.get('eps_status','-')))}</td><td>{escape(str(why.get('least_resistance','-')))}</td>"
            f"<td>{escape(str(risk_plan.get('entry')))}</td><td>{escape(str(risk_plan.get('stop')))}</td>"
            f"<td>{escape(str(risk_plan.get('target')))}</td><td>{escape(str(risk_plan.get('rr_ratio')))}</td></tr>"
        )

    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Minervini Recommendations</title>
  <style>
    body {{ font-family: Arial, sans-serif; padding: 16px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
  </style>
</head>
<body>
  <h2>Minervini Recommendations - {format_date_token(date_dir)}</h2>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Symbol</th><th>Sector</th><th>Conviction</th><th>Score</th>
        <th>EPS</th><th>Least Resistance</th><th>Entry</th><th>Stop</th><th>Target</th><th>R/R</th>
      </tr>
    </thead>
    <tbody>{''.join(rows) if rows else '<tr><td colspan="11">No recommendations</td></tr>'}</tbody>
  </table>
</body>
</html>
"""
    path.write_text(html, encoding='utf-8')


def _read_delta(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding='utf-8'))
    # Handle envelope-wrapped output
    if isinstance(data, dict) and 'items' in data:
        return data['items']
    if isinstance(data, list):
        return data
    return []


def _should_write_latest(date_dir: str) -> bool:
    if not LATEST_PATH.exists():
        return True
    try:
        latest = json.loads(LATEST_PATH.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return True
    return date_dir >= str(latest.get('date_dir', '0'))


def build_after_close(as_of_date: str | None = None, refresh_live: bool = True) -> str:
    date_dir = normalize_date_token(as_of_date) or datetime.now().strftime('%Y%m%d')
    if refresh_live and not as_of_date:
        run_live_cycle()
    else:
        run_pipeline(as_of_date=date_dir, refresh_live=False)

    out = Path(f'data/daily-signals/{date_dir}')
    leaders = MinerviniLeaders()
    sectors, stocks = leaders.run(date_dir, as_of_date=date_dir)

    write_json(out / 'leader-sectors.json', wrap_output(sectors, date_dir=date_dir))
    write_json(out / 'leader-stocks.json', wrap_output(stocks, date_dir=date_dir))

    grouped = leaders.run_grouped(date_dir, as_of_date=date_dir, per_sector_n=5)
    write_json(out / 'leader-sectors-grouped.json', wrap_output(grouped, date_dir=date_dir))

    delta = _read_delta(out / 'delta-risk-plan.json')
    recs = MinerviniRecommender(top_n=5).run(stocks, delta, as_of_date=date_dir)
    write_json(out / 'recommendations.json', wrap_output(recs, date_dir=date_dir))

    write_report(out / 'daily-leaders-report.md', date_dir, sectors, stocks, recs)
    write_html_report(out / 'recommendations-report.html', date_dir, recs)

    briefing = build_briefing(date_dir, sectors, recs)
    write_json(out / 'briefing.json', wrap_output(briefing, date_dir=date_dir))
    (out / 'briefing.md').write_text('# Daily Briefing\n\n' + briefing['message_ko'], encoding='utf-8')

    # Market Wizards multi-strategy screening
    try:
        wizard_results = run_wizard_screen(date_dir)
        write_json(out / 'wizard-screen.json', wrap_output(wizard_results, date_dir=date_dir))
        print(f'  wizard-screen: {wizard_results.get("stocks_passing_any", 0)} stocks matched')
    except (ValueError, TypeError, KeyError, OSError) as exc:
        logger.warning('wizard-screen skipped: %s', exc)
        print(f'  wizard-screen skipped: {exc}')

    # Preset picks: screen all 25 presets for today's picks
    try:
        preset_picks = _generate_preset_picks(date_dir)
        write_json(out / 'preset-picks.json', wrap_output(preset_picks, date_dir=date_dir))
        total_picks = sum(len(v.get('items', [])) for v in preset_picks.values())
        print(f'  preset-picks: {len(preset_picks)} presets, {total_picks} total picks')
    except Exception as exc:
        logger.warning('preset-picks skipped: %s', exc)
        print(f'  preset-picks skipped: {exc}')

    upsert_daily(date_dir, recs, briefing=briefing, sectors=sectors, stocks=stocks)
    if _should_write_latest(date_dir):
        write_json(LATEST_PATH, {'date_dir': date_dir})

    print(f'[OK] after-close leaders generated: {out} | recommendations={len(recs)}')
    return date_dir


def _generate_preset_picks(date_dir: str) -> dict:
    """Screen all presets and return {preset_id: {items, strategy, ...}}."""
    from sepa.backtest.presets import PRESETS
    from sepa.backtest.screener import screen_universe
    from sepa.data.ohlcv_db import read_ohlcv_batch

    price_data = read_ohlcv_batch(min_rows=200)
    if not price_data:
        return {}

    result = {}
    for preset_id, config in PRESETS.items():
        try:
            picks = screen_universe(config, price_data)[:config.max_positions]
            result[preset_id] = {
                'strategy': config.name,
                'family': config.family,
                'description': config.description,
                'items': [
                    {
                        'symbol': p.get('symbol'),
                        'name': p.get('name'),
                        'sector': p.get('sector'),
                        'score': round(min(p.get('score', 0), 100), 1),
                        'rs_percentile': p.get('rs_percentile'),
                        'tt_passed': p.get('tt_passed'),
                        'execution': p.get('execution'),
                    }
                    for p in picks
                ],
            }
        except Exception:
            result[preset_id] = {'strategy': config.name, 'items': [], 'error': True}

    return result


def main() -> None:
    build_after_close()


if __name__ == '__main__':
    main()
