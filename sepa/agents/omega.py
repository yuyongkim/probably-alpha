from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path


class OmegaPM:
    def run(self, risk_plans: list[dict], output_dir: Path | None = None) -> dict:
        today = datetime.now().strftime('%Y-%m-%d')
        picks = risk_plans[:3]
        payload = {
            'date': today,
            'final_picks': picks,
            'note': 'rule-based final selection',
        }

        if output_dir is not None:
            self._write_html_report(output_dir, payload)

        return payload

    def _write_html_report(self, output_dir: Path, payload: dict) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        rows = []
        for p in payload.get('final_picks', []):
            rows.append(
                f"<tr><td>{escape(str(p['symbol']))}</td><td>{escape(str(p['entry']))}</td><td>{escape(str(p['stop']))}</td>"
                f"<td>{escape(str(p['target']))}</td><td>{escape(str(p['qty']))}</td><td>{escape(str(p['rr_ratio']))}</td></tr>"
            )
        table = '\n'.join(rows) if rows else '<tr><td colspan="6">No picks</td></tr>'
        html = f"""
<!doctype html>
<html><head><meta charset='utf-8'><title>Omega Report</title></head>
<body>
  <h2>Omega Final Picks - {escape(str(payload.get('date', '')))}</h2>
  <table border='1' cellpadding='6' cellspacing='0'>
    <thead><tr><th>Symbol</th><th>Entry</th><th>Stop</th><th>Target</th><th>Qty</th><th>R/R</th></tr></thead>
    <tbody>{table}</tbody>
  </table>
</body></html>
""".strip()
        (output_dir / 'omega-report.html').write_text(html, encoding='utf-8')
