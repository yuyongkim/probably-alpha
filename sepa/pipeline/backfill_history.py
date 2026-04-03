from __future__ import annotations

import argparse
import logging

from sepa.data.price_history import available_dates
from sepa.pipeline.run_after_close import build_after_close
from sepa.storage.recommendation_store import snapshot_exists, snapshot_needs_refresh

logger = logging.getLogger(__name__)


def _select_dates(days: int | None = None, date_from: str | None = None, date_to: str | None = None) -> list[str]:
    dates = available_dates()
    if date_from:
        dates = [item for item in dates if item >= date_from]
    if date_to:
        dates = [item for item in dates if item <= date_to]
    if days:
        dates = dates[-days:]
    return dates


def backfill_history(
    days: int | None = 84,
    date_from: str | None = None,
    date_to: str | None = None,
    force: bool = False,
) -> list[str]:
    built: list[str] = []
    for date_dir in _select_dates(days=days, date_from=date_from, date_to=date_to):
        if not force and snapshot_exists(date_dir) and not snapshot_needs_refresh(date_dir):
            continue
        try:
            build_after_close(as_of_date=date_dir, refresh_live=False)
            built.append(date_dir)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            logger.error('backfill failed for %s: %s', date_dir, exc)
            print(f'[ERROR] backfill failed for {date_dir}: {exc}')
    return built


def main() -> None:
    parser = argparse.ArgumentParser(description='Backfill daily Minervini snapshots for history/backtests.')
    parser.add_argument('--days', type=int, default=84, help='Most recent dates to backfill')
    parser.add_argument('--date-from', dest='date_from', help='Inclusive YYYYMMDD lower bound')
    parser.add_argument('--date-to', dest='date_to', help='Inclusive YYYYMMDD upper bound')
    parser.add_argument('--force', action='store_true', help='Rebuild snapshots even if they already exist')
    args = parser.parse_args()

    built = backfill_history(days=args.days, date_from=args.date_from, date_to=args.date_to, force=args.force)
    print(f'[OK] backfill complete | built={len(built)}')


if __name__ == '__main__':
    main()
