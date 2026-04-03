from __future__ import annotations

from sepa.agents.execution_plan import ExecutionPlanner


class DeltaRiskManager:
    """Build price-aware execution plans for the strongest Gamma candidates."""

    def __init__(self) -> None:
        self.planner = ExecutionPlanner()

    def run(self, gamma_payload: dict, as_of_date: str | None = None) -> list[dict]:
        items = gamma_payload.get('general', []) if isinstance(gamma_payload, dict) else []
        plans = []

        for item in items[:3]:
            symbol = item.get('symbol', 'UNKNOWN')
            gamma_score = round(float(item.get('gamma_score', 0.0)), 2)

            plan = self.planner.build_plan(symbol, as_of_date=as_of_date)
            if plan.get('entry') is None:
                continue

            plans.append(
                {
                    'symbol': symbol,
                    'name': plan.get('name', symbol),
                    'entry': plan.get('entry'),
                    'stop': plan.get('stop'),
                    'target': plan.get('target'),
                    'qty': plan.get('qty'),
                    'rr_ratio': plan.get('rr_ratio'),
                    'gamma_score': gamma_score,
                }
            )

        return plans
