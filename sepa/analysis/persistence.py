from __future__ import annotations

from functools import lru_cache
from statistics import mean

from sepa.data.price_history import leading_available_dates, nearest_available_date, trailing_available_dates
from sepa.storage.recommendation_store import get_snapshots


def _series_for_key(
    rows_by_date: dict[str, dict],
    dates: list[str],
    *,
    kind: str,
    key: str,
    top_n: int,
) -> list[dict]:
    field = 'sector' if kind == 'sector' else 'symbol'
    bucket_name = 'sectors' if kind == 'sector' else 'stocks'
    score_field = 'leader_score' if kind == 'sector' else 'leader_stock_score'

    out: list[dict] = []
    for date_dir in dates:
        row = rows_by_date.get(date_dir)
        items = list((row or {}).get(bucket_name, []))[:top_n]
        match = next((item for item in items if str(item.get(field, '')) == key), None)
        out.append(
            {
                'date_dir': date_dir,
                'present': bool(match),
                'rank': (items.index(match) + 1) if match else None,
                'score': float(match.get(score_field, 0.0)) if match else None,
            }
        )
    return out


def _streak_from_end(series: list[dict]) -> int:
    streak = 0
    for item in reversed(series):
        if not item['present']:
            break
        streak += 1
    return streak


def _streak_from_start(series: list[dict]) -> int:
    streak = 0
    for item in series:
        if not item['present']:
            break
        streak += 1
    return streak


def _max_streak(series: list[dict]) -> int:
    best = 0
    current = 0
    for item in series:
        if item['present']:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


@lru_cache(maxsize=256)
def build_persistence(
    *,
    kind: str,
    key: str,
    date_to: str | None = None,
    lookback_days: int = 126,
    forward_days: int = 126,
    top_n: int | None = None,
) -> dict:
    kind_key = str(kind or 'stock').strip().lower()
    if kind_key not in {'sector', 'stock'}:
        raise ValueError(f'unsupported kind: {kind}')

    limit = top_n or (5 if kind_key == 'sector' else 10)
    resolved = nearest_available_date(date_to)
    if not resolved:
        return {
            'kind': kind_key,
            'key': key,
            'resolved_date': '',
            'lookback_days': 0,
            'forward_days': 0,
            'appearance_count': 0,
            'appearance_ratio': 0.0,
            'current_streak': 0,
            'max_streak': 0,
            'forward_streak': 0,
            'avg_rank': None,
            'top1_count': 0,
            'avg_score_when_present': 0.0,
            'persistence_score': 0.0,
            'logic': {},
        }

    trailing_dates = trailing_available_dates(resolved, length=lookback_days)
    forward_dates = leading_available_dates(resolved, length=forward_days)
    date_from = trailing_dates[0] if trailing_dates else resolved
    future_to = forward_dates[-1] if forward_dates else resolved
    snapshots = get_snapshots(date_from=date_from, date_to=future_to, descending=False, limit=None)
    rows_by_date = {row['date_dir']: row for row in snapshots}

    past_series = _series_for_key(rows_by_date, trailing_dates, kind=kind_key, key=key, top_n=limit)
    future_series = _series_for_key(rows_by_date, forward_dates, kind=kind_key, key=key, top_n=limit)
    present_rows = [item for item in past_series if item['present']]
    appearances = len(present_rows)
    lookback_count = len(trailing_dates)
    forward_count = len(forward_dates)
    avg_rank = mean(item['rank'] for item in present_rows) if present_rows else None
    avg_score = mean(item['score'] for item in present_rows if item['score'] is not None) if present_rows else 0.0
    top1_count = sum(1 for item in present_rows if item['rank'] == 1)

    appearance_ratio = appearances / lookback_count if lookback_count else 0.0
    current_streak = _streak_from_end(past_series)
    max_streak = _max_streak(past_series)
    forward_streak = _streak_from_start(future_series)
    current_streak_ratio = current_streak / lookback_count if lookback_count else 0.0
    max_streak_ratio = max_streak / lookback_count if lookback_count else 0.0
    rank_strength = 1.0 - ((avg_rank - 1.0) / max(1.0, limit - 1.0)) if avg_rank is not None else 0.0
    top1_ratio = top1_count / lookback_count if lookback_count else 0.0

    persistence_score = 100.0 * (
        appearance_ratio * 0.35
        + current_streak_ratio * 0.25
        + max_streak_ratio * 0.20
        + rank_strength * 0.15
        + top1_ratio * 0.05
    )

    return {
        'kind': kind_key,
        'key': key,
        'resolved_date': resolved,
        'lookback_days': lookback_count,
        'forward_days': forward_count,
        'top_n': limit,
        'appearance_count': appearances,
        'appearance_ratio': round(appearance_ratio, 4),
        'current_streak': current_streak,
        'max_streak': max_streak,
        'forward_streak': forward_streak,
        'avg_rank': round(avg_rank, 2) if avg_rank is not None else None,
        'top1_count': top1_count,
        'first_seen': present_rows[0]['date_dir'] if present_rows else None,
        'last_seen': present_rows[-1]['date_dir'] if present_rows else None,
        'avg_score_when_present': round(avg_score, 2),
        'persistence_score': round(persistence_score, 2),
        'logic': {
            'expression': (
                'persistence_score = 100 x (0.35 x appearance_ratio + 0.25 x current_streak_ratio '
                '+ 0.20 x max_streak_ratio + 0.15 x rank_strength + 0.05 x top1_ratio)'
            ),
            'meaning': (
                '얼마나 자주 상위권에 나왔는지, 지금도 이어지고 있는지, 과거 최대 연속성, '
                '평균 랭크 강도, 1위 점유 비율을 합쳐 지속성을 본다.'
            ),
        },
    }
