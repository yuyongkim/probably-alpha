from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sepa.agents.alpha import AlphaScreener
from sepa.agents.beta import BetaChartist
from sepa.agents.gamma import GammaResearcher
from sepa.agents.delta import DeltaRiskManager
from sepa.agents.omega import OmegaPM
from sepa.contracts.envelope import reset_run_id, wrap_output
from sepa.data.price_history import normalize_date_token


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _maybe_refresh_live_data(enabled: bool) -> None:
    if not enabled:
        return
    if os.getenv('SEPA_LIVE_MODE', '0').strip() != '1':
        return
    from sepa.pipeline.refresh_market_data import main as refresh_main

    refresh_main()


def run_pipeline(as_of_date: str | None = None, refresh_live: bool = True) -> str:
    date_dir = normalize_date_token(as_of_date) or datetime.now().strftime('%Y%m%d')
    reset_run_id()
    _maybe_refresh_live_data(enabled=refresh_live and not as_of_date)

    out = Path(f'.omx/artifacts/daily-signals/{date_dir}')

    alpha = AlphaScreener().run(as_of_date=date_dir)
    write_json(out / 'alpha-passed.json', wrap_output(alpha, date_dir=date_dir))

    beta = BetaChartist().run(alpha, as_of_date=date_dir)
    write_json(out / 'beta-vcp-candidates.json', wrap_output(beta, date_dir=date_dir))

    gamma = GammaResearcher().run(beta, as_of_date=date_dir)
    write_json(out / 'gamma-insights.json', wrap_output(gamma, date_dir=date_dir))
    write_json(out / 'gamma-chem-insights.json', wrap_output(gamma.get('chem', []), date_dir=date_dir))

    delta = DeltaRiskManager().run(gamma, as_of_date=date_dir)
    write_json(out / 'delta-risk-plan.json', wrap_output(delta, date_dir=date_dir))

    omega = OmegaPM().run(delta, output_dir=out)
    write_json(out / 'omega-final-picks.json', wrap_output(omega, date_dir=date_dir))

    print(
        f"[OK] saved to {out} | alpha={len(alpha)} beta={len(beta)} "
        f"gamma={len(gamma.get('general', []))} delta={len(delta)} picks={len(omega.get('final_picks', []))}"
    )
    return date_dir


def main() -> None:
    as_of_date = os.getenv('SEPA_AS_OF_DATE', '').strip() or None
    run_pipeline(as_of_date=as_of_date, refresh_live=True)


if __name__ == '__main__':
    main()
