from __future__ import annotations

import json
from pathlib import Path

from sepa.agents.execution_plan import ExecutionPlanner
from sepa.analysis.stock_analysis import build_stock_analysis


class MinerviniRecommender:
    def __init__(self, top_n: int = 3, config_path: Path = Path('config/minervini_config.json')) -> None:
        self.top_n = top_n
        self.planner = ExecutionPlanner(config_path=config_path)

        self.weights = {
            'alpha': 0.45,
            'beta': 0.20,
            'gamma': 0.20,
            'rs120': 0.10,
            'least_resistance': 0.05,
        }
        self.eps_allowed = {'strong_growth', 'positive_growth'}
        self.lr_allowed = {'up_least_resistance', 'pullback_in_uptrend'}
        self.min_score = 40.0

        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding='utf-8'))
                self.weights.update(cfg.get('weights', {}))
                g = cfg.get('gates', {})
                self.eps_allowed = set(g.get('eps_status_allowed', list(self.eps_allowed)))
                self.lr_allowed = set(g.get('least_resistance_allowed', list(self.lr_allowed)))
                self.min_score = float(g.get('min_recommendation_score', self.min_score))
            except Exception:
                pass

    def run(self, leader_stocks: list[dict], delta_plans: list[dict], as_of_date: str | None = None) -> list[dict]:
        delta_map = {x.get('symbol'): x for x in (delta_plans or [])}
        out = []

        for s in leader_stocks:
            sym = s.get('symbol', '')
            if not sym:
                continue
            if not s.get('sector_leadership_ready'):
                continue

            analysis = build_stock_analysis(sym, as_of_date=as_of_date)
            eps_status = analysis.get('eps_quality', {}).get('status', 'missing')
            lr_trend = analysis.get('least_resistance', {}).get('trend', 'unknown')
            lr_dist = float(analysis.get('least_resistance', {}).get('distance_pct', 0.0))

            if eps_status not in self.eps_allowed:
                continue
            if lr_trend not in self.lr_allowed:
                continue

            alpha = float(s.get('alpha_score', 0.0))
            beta = float(s.get('beta_confidence', 0.0))
            gamma = float(s.get('gamma_score', 0.0))
            rs = float(s.get('ret120', 0.0)) * 100.0
            lr_bonus = 100.0 if lr_trend == 'up_least_resistance' else max(0.0, 80.0 - abs(lr_dist))

            score = (
                alpha * float(self.weights.get('alpha', 0.45))
                + beta * 10.0 * float(self.weights.get('beta', 0.20))
                + gamma * 10.0 * float(self.weights.get('gamma', 0.20))
                + rs * float(self.weights.get('rs120', 0.10))
                + lr_bonus * float(self.weights.get('least_resistance', 0.05))
            )

            if score < self.min_score:
                continue

            risk = delta_map.get(sym, {})
            if not risk or risk.get('entry') is None:
                risk = self.planner.build_plan(sym, as_of_date=as_of_date)

            conviction = self._conviction(score, eps_status, lr_trend)

            out.append(
                {
                    'symbol': sym,
                    'name': s.get('name', sym),
                    'sector': s.get('sector', '기타'),
                    'recommendation_score': round(score, 2),
                    'conviction': conviction,
                    'why': {
                        'alpha_score': round(alpha, 2),
                        'beta_confidence': round(beta, 2),
                        'gamma_score': round(gamma, 2),
                        'eps_status': eps_status,
                        'least_resistance': lr_trend,
                        'ret120_pct': round(rs, 2),
                    },
                    'risk_plan': {
                        'entry': risk.get('entry'),
                        'stop': risk.get('stop'),
                        'target': risk.get('target'),
                        'qty': risk.get('qty'),
                        'rr_ratio': risk.get('rr_ratio'),
                    },
                }
            )

        out.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return out[: self.top_n]

    @staticmethod
    def _conviction(score: float, eps_status: str, lr_trend: str) -> str:
        if score >= 70 and eps_status == 'strong_growth' and lr_trend == 'up_least_resistance':
            return 'A+'
        if score >= 60:
            return 'A'
        if score >= 50:
            return 'B'
        return 'C'
