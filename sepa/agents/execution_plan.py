from __future__ import annotations

import json
import logging
from pathlib import Path

from sepa.analysis.stock_analysis import build_stock_analysis
from sepa.data.universe import get_symbol_name

logger = logging.getLogger(__name__)


class ExecutionPlanner:
    """추천 종목에 대해 Minervini식 실행 계획(진입/손절/목표) 생성."""

    def __init__(self, config_path: Path = Path('config/minervini_config.json')) -> None:
        self.stop_loss_pct = 0.075
        self.target_r_multiple = 2.0
        self.risk_budget = 200000.0
        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding='utf-8'))
                r = cfg.get('risk', {})
                self.stop_loss_pct = float(r.get('stop_loss_pct', self.stop_loss_pct))
                self.target_r_multiple = float(r.get('target_r_multiple', self.target_r_multiple))
                self.risk_budget = float(r.get('risk_budget_krw', self.risk_budget))
            except (json.JSONDecodeError, ValueError, TypeError, OSError) as exc:
                logger.warning('config load failed (%s), using defaults: %s', config_path, exc)

    def build_plan(self, symbol: str, as_of_date: str | None = None) -> dict:
        a = build_stock_analysis(symbol, as_of_date=as_of_date)
        closes = [x.get('close', 0.0) for x in a.get('close_series', []) if x.get('close')]
        if not closes:
            return {'entry': None, 'stop': None, 'target': None, 'qty': None, 'rr_ratio': None}

        last = float(closes[-1])
        lr = a.get('least_resistance', {})
        line = float(lr.get('line_last', last) or last)

        entry_base = max(last, line)
        entry = round(entry_base * 1.005, 2)

        stop = round(entry * (1.0 - self.stop_loss_pct), 2)

        risk = max(0.01, entry - stop)
        target = round(entry + risk * self.target_r_multiple, 2)
        rr = round((target - entry) / risk, 2)

        qty = int(self.risk_budget // risk) if risk > 0 else 0
        if qty < 1:
            qty = 1

        # --- Volume surge gate (Minervini breakout confirmation) ---
        volume_signal = a.get('volume_signal', {})
        volume_surge_ratio = float(volume_signal.get('latest_ratio_20') or 0.0)
        volume_surge_confirmed = volume_surge_ratio >= 1.4
        entry_note = None if volume_surge_confirmed else 'awaiting_volume_surge'

        return {
            'symbol': symbol,
            'name': get_symbol_name(symbol),
            'entry': entry,
            'stop': stop,
            'target': target,
            'qty': qty,
            'rr_ratio': rr,
            'volume_surge_ratio': round(volume_surge_ratio, 3),
            'volume_surge_confirmed': volume_surge_confirmed,
            'entry_note': entry_note,
        }
