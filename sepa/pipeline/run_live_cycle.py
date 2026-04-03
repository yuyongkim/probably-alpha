from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

SUBPROCESS_TIMEOUT_SEC = 600  # 10 minutes


def run(cmd: list[str]) -> int:
    try:
        p = subprocess.run(cmd, timeout=SUBPROCESS_TIMEOUT_SEC)
        return p.returncode
    except subprocess.TimeoutExpired:
        logger.error('subprocess timed out after %ds: %s', SUBPROCESS_TIMEOUT_SEC, ' '.join(cmd))
        return 1


def main() -> None:
    steps = [
        [sys.executable, '-m', 'sepa.pipeline.refresh_market_data'],
        [sys.executable, '-m', 'sepa.pipeline.run_mvp'],
        [sys.executable, '-m', 'sepa.pipeline.validate_outputs'],
    ]
    for s in steps:
        print('\n>>', ' '.join(s))
        code = run(s)
        if code != 0:
            raise SystemExit(code)


if __name__ == '__main__':
    main()
