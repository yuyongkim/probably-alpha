"""Auto-backfill: refresh market data and fill any missing daily signals.

Designed to run automatically on Windows logon via Task Scheduler.
Catches up all missing dates since the last snapshot, then exits.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force live refresh so kiwoom/yfinance data always overwrites stale CSVs
os.environ.setdefault('SEPA_FORCE_LIVE_REFRESH', '1')

from sepa.pipeline.refresh_market_data import main as refresh_market_data
from sepa.pipeline.backfill_history import backfill_history
from sepa.pipeline.run_after_close import build_after_close
from sepa.storage.recommendation_store import snapshot_exists


def main() -> None:
    today = datetime.now().strftime('%Y%m%d')
    print(f'[auto-backfill] {today} - refreshing market data...')

    try:
        refresh_market_data()
    except Exception as exc:
        print(f'[auto-backfill] market data refresh failed: {exc}')
        print('[auto-backfill] continuing with backfill using cached data...')

    # 1) Backfill any missing past dates
    print('[auto-backfill] backfilling missing dates (last 30 trading days)...')
    built = backfill_history(days=30)
    if built:
        print(f'[auto-backfill] filled {len(built)} dates: {built[0]} -> {built[-1]}')
    else:
        print('[auto-backfill] past dates already up to date')

    # 2) Always generate today's signals (even if backfill didn't cover it)
    if not snapshot_exists(today):
        print(f'[auto-backfill] building today ({today}) signals...')
        try:
            build_after_close(as_of_date=today, refresh_live=False)
            print(f'[auto-backfill] today ({today}) signals generated')
        except Exception as exc:
            print(f'[auto-backfill] today build failed: {exc}')
    else:
        print(f'[auto-backfill] today ({today}) snapshot already exists')

    # 3) Generate trader debate for today
    try:
        from scripts.generate_debate import collect_market_data, build_rule_based_debate
        import json
        debate_path = ROOT / f'.omx/artifacts/daily-signals/{today}/trader-debate.json'
        if not debate_path.exists():
            data = collect_market_data(today)
            debate = build_rule_based_debate(data)
            debate_path.parent.mkdir(parents=True, exist_ok=True)
            debate_path.write_text(json.dumps(debate, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f'[auto-backfill] trader debate generated for {today}')
    except Exception as exc:
        print(f'[auto-backfill] trader debate skipped: {exc}')

    print('[auto-backfill] done')


if __name__ == '__main__':
    main()
