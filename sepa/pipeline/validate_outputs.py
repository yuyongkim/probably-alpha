from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def _load(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def main() -> None:
    d = datetime.now().strftime('%Y%m%d')
    base = Path(f'.omx/artifacts/daily-signals/{d}')
    errs: list[str] = []

    alpha = _load(base / 'alpha-passed.json') if (base / 'alpha-passed.json').exists() else []
    for r in alpha:
        if 'symbol' not in r or 'score' not in r:
            errs.append('alpha row missing symbol/score')

    beta = _load(base / 'beta-vcp-candidates.json') if (base / 'beta-vcp-candidates.json').exists() else []
    for r in beta:
        c = float(r.get('confidence', -1))
        if not (0 <= c <= 10):
            errs.append(f"beta confidence out of range: {r.get('symbol')}")

    delta = _load(base / 'delta-risk-plan.json') if (base / 'delta-risk-plan.json').exists() else []
    for r in delta:
        rr = float(r.get('rr_ratio', 0))
        if rr < 1.5:
            errs.append(f"delta rr<1.5: {r.get('symbol')}")

    status = 'PASS' if not errs else 'FAIL'
    report = {'date': d, 'status': status, 'errors': errs}
    out = Path('.omx/artifacts/audit-logs/verification-report.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"[{status}] validation report: {out}")


if __name__ == '__main__':
    main()
