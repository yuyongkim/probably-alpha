from __future__ import annotations

from datetime import datetime

from sepa.data.dart import DartProvider
from sepa.data.macro import MacroDataProvider
from sepa.data.quantdb import read_company_snapshot
from sepa.data.universe import get_symbol_name


class GammaResearcher:
    """Adds Minervini-style EPS acceleration and a small macro overlay."""

    def __init__(self) -> None:
        self.macro = MacroDataProvider()
        self.dart = DartProvider()

    def run(self, beta_candidates: list[dict], as_of_date: str | None = None) -> dict:
        snap = self._macro_snapshot(as_of_date)
        general = []
        chem = []

        for row in beta_candidates:
            symbol = row.get('symbol', 'UNKNOWN')
            vcp_conf = float(row.get('confidence', 0.0))
            growth = self.dart.get_growth_hint(symbol, as_of_date=as_of_date)
            growth_hint = float(growth.get('growth_hint', 0.5))
            fundamental_score = min(10.0, 4.0 + vcp_conf * 0.5 + growth_hint * 2.0)

            # --- Minervini fundamental quality screening ---
            snapshot = read_company_snapshot(symbol)
            roe = float(snapshot.get('roe') or 0.0) if snapshot else 0.0
            opm = float(snapshot.get('opm') or 0.0) if snapshot else 0.0

            fq_bonus = 0.0
            if roe >= 20:
                fq_bonus += 1.0
            elif roe >= 15:
                fq_bonus += 0.5
            if opm >= 15:
                fq_bonus += 0.5
            elif opm >= 10:
                fq_bonus += 0.3

            chem_bonus = 0.0
            if symbol.startswith('0519'):
                chem_bonus += 0.8
            if isinstance(snap.get('wti'), (int, float)):
                wti = float(snap['wti'])
                if 55 <= wti <= 95:
                    chem_bonus += 0.4

            total = round(min(10.0, fundamental_score + fq_bonus + chem_bonus), 2)
            item = {
                'symbol': symbol,
                'name': get_symbol_name(symbol),
                'vcp_confidence': round(vcp_conf, 2),
                'fundamental_score': round(fundamental_score, 2),
                'chem_bonus': round(chem_bonus, 2),
                'growth_hint': round(growth_hint, 2),
                'eps_status': growth.get('status', 'missing'),
                'eps_yoy': round(float(growth.get('latest_yoy', 0.0)), 2),
                'eps_acceleration': round(float(growth.get('acceleration', 0.0)), 2),
                'roe': round(roe, 2),
                'opm': round(opm, 2),
                'fundamental_quality_bonus': round(fq_bonus, 2),
                'gamma_score': total,
            }
            general.append(item)
            if chem_bonus > 0:
                chem.append(item)

        general.sort(key=lambda x: x['gamma_score'], reverse=True)
        chem.sort(key=lambda x: x['gamma_score'], reverse=True)

        return {
            'as_of': (as_of_date or datetime.now().strftime('%Y-%m-%d')),
            'macro_snapshot': snap,
            'general': general,
            'chem': chem,
        }

    def _macro_snapshot(self, as_of_date: str | None) -> dict:
        today = datetime.now().strftime('%Y%m%d')
        if as_of_date and as_of_date != today:
            return {
                'as_of': as_of_date,
                'source': 'historical-neutral',
                'wti': None,
                'fred_pmi_proxy': None,
                'ecos_rate': None,
            }
        return self.macro.get_snapshot()
