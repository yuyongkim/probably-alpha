from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from sepa.data.price_history import is_business_date_token

DB_PATH = Path('.omx/artifacts/recommendations.db')
_SCHEMA_READY = False
_SCHEMA_LOCK = threading.Lock()


def _conn() -> sqlite3.Connection:
    global _SCHEMA_READY
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    if not _SCHEMA_READY:
        with _SCHEMA_LOCK:
            if not _SCHEMA_READY:
                conn.execute(
                    '''
                    create table if not exists daily_recommendations (
                        date_dir text primary key,
                        created_at text,
                        recommendations_json text not null,
                        briefing_json text,
                        sectors_json text,
                        stocks_json text
                    )
                    '''
                )
                _SCHEMA_READY = True
    return conn


def upsert_daily(
    date_dir: str,
    recommendations: list[dict],
    briefing: dict | None = None,
    sectors: list[dict] | None = None,
    stocks: list[dict] | None = None,
) -> None:
    with _conn() as conn:
        conn.execute(
            '''
            insert into daily_recommendations
            (date_dir, created_at, recommendations_json, briefing_json, sectors_json, stocks_json)
            values (?, datetime('now'), ?, ?, ?, ?)
            on conflict(date_dir) do update set
              created_at=excluded.created_at,
              recommendations_json=excluded.recommendations_json,
              briefing_json=excluded.briefing_json,
              sectors_json=excluded.sectors_json,
              stocks_json=excluded.stocks_json
            ''',
            (
                date_dir,
                json.dumps(recommendations, ensure_ascii=False),
                json.dumps(briefing or {}, ensure_ascii=False),
                json.dumps(sectors or [], ensure_ascii=False),
                json.dumps(stocks or [], ensure_ascii=False),
            ),
        )


def snapshot_exists(date_dir: str) -> bool:
    with _conn() as conn:
        row = conn.execute('select 1 from daily_recommendations where date_dir = ? limit 1', (date_dir,)).fetchone()
    return bool(row)


def snapshot_needs_refresh(date_dir: str) -> bool:
    snapshot = get_snapshot(date_dir)
    if not snapshot:
        return True

    def missing_name(items: list[dict]) -> bool:
        return any(not str(item.get('name', '')).strip() for item in items)

    return missing_name(snapshot.get('recommendations', [])) or missing_name(snapshot.get('stocks', []))


def get_snapshot(date_dir: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            '''
            select date_dir, recommendations_json, briefing_json, sectors_json, stocks_json
            from daily_recommendations
            where date_dir = ?
            ''',
            (date_dir,),
        ).fetchone()
    return _decode_snapshot_row(row)


def get_latest() -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            '''
            select date_dir, recommendations_json, briefing_json, sectors_json, stocks_json
            from daily_recommendations
            order by date_dir desc
            limit 1
            '''
        ).fetchone()
    return _decode_snapshot_row(row)


def get_history(date_from: str | None = None, date_to: str | None = None, limit: int = 60) -> list[dict]:
    rows = _fetch_snapshot_rows(date_from=date_from, date_to=date_to, limit=limit, descending=True)
    out = []
    for row in rows:
        recs = row['recommendations']
        out.append({'date_dir': row['date_dir'], 'top3': recs[:3], 'count': len(recs)})
    return out


def get_snapshots(
    date_from: str | None = None,
    date_to: str | None = None,
    descending: bool = False,
    limit: int | None = None,
) -> list[dict]:
    return _fetch_snapshot_rows(date_from=date_from, date_to=date_to, limit=limit, descending=descending)


def get_snapshot_bounds() -> dict:
    with _conn() as conn:
        row = conn.execute(
            '''
            select min(date_dir), max(date_dir), count(*)
            from daily_recommendations
            '''
        ).fetchone()
    return {
        'min_date': row[0] if row and row[0] else None,
        'max_date': row[1] if row and row[1] else None,
        'count': int(row[2] or 0) if row else 0,
    }


def get_leader_buckets(
    period: str = 'weekly',
    date_from: str | None = None,
    date_to: str | None = None,
    bucket_limit: int = 8,
    sector_limit: int = 5,
    stock_limit: int = 10,
) -> list[dict]:
    rows = _fetch_backtest_rows(
        date_from=date_from,
        date_to=date_to,
        limit=None if date_from and date_to else max(bucket_limit * 14, 60),
        descending=not (date_from and date_to),
    )
    if not rows:
        return []
    if date_from is None and date_to is None:
        rows = list(reversed(rows))

    period_key = str(period or 'weekly').strip().lower()
    if period_key not in {'daily', 'weekly'}:
        raise ValueError(f'unsupported period: {period}')

    if period_key == 'daily':
        buckets = [
            {
                'bucket': row['date_dir'],
                'date_from': row['date_dir'],
                'date_to': row['date_dir'],
                'snapshot_count': 1,
                'sectors': row['sectors'][:sector_limit],
                'stocks': row['stocks'][:stock_limit],
            }
            for row in rows
        ]
        return list(reversed(buckets))[:bucket_limit]

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        bucket = _weekly_bucket(row['date_dir'])
        grouped.setdefault(bucket, []).append(row)

    out = []
    for bucket, bucket_rows in grouped.items():
        ordered = sorted(bucket_rows, key=lambda item: item['date_dir'])
        out.append(
            {
                'bucket': bucket,
                'date_from': ordered[0]['date_dir'],
                'date_to': ordered[-1]['date_dir'],
                'snapshot_count': len(ordered),
                'sectors': _aggregate_sectors(ordered, limit=sector_limit),
                'stocks': _aggregate_stocks(ordered, limit=stock_limit),
            }
        )

    out.sort(key=lambda item: item['date_to'], reverse=True)
    return out[:bucket_limit]


def _fetch_backtest_rows(
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int | None = 60,
    descending: bool = True,
) -> list[dict]:
    query = (
        'select date_dir, sectors_json, stocks_json '
        'from daily_recommendations where 1=1'
    )
    params: list = []
    if date_from:
        query += ' and date_dir >= ?'
        params.append(date_from)
    if date_to:
        query += ' and date_dir <= ?'
        params.append(date_to)
    query += f" order by date_dir {'desc' if descending else 'asc'}"
    if limit is not None:
        query += ' limit ?'
        params.append(limit)

    with _conn() as conn:
        raw_rows = conn.execute(query, params).fetchall()

    out: list[dict] = []
    for row in raw_rows:
        date_dir = row[0]
        if not is_business_date_token(date_dir):
            continue
        out.append(
            {
                'date_dir': date_dir,
                'recommendations': [],
                'briefing': {},
                'sectors': json.loads(row[1] or '[]'),
                'stocks': json.loads(row[2] or '[]'),
            }
        )
    return out


def _fetch_snapshot_rows(
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int | None = 60,
    descending: bool = True,
) -> list[dict]:
    query = (
        'select date_dir, recommendations_json, briefing_json, sectors_json, stocks_json '
        'from daily_recommendations where 1=1'
    )
    params: list = []
    if date_from:
        query += ' and date_dir >= ?'
        params.append(date_from)
    if date_to:
        query += ' and date_dir <= ?'
        params.append(date_to)
    query += f" order by date_dir {'desc' if descending else 'asc'}"
    if limit is not None:
        query += ' limit ?'
        params.append(limit)

    with _conn() as conn:
        raw_rows = conn.execute(query, params).fetchall()
    return [
        decoded
        for row in raw_rows
        for decoded in [_decode_snapshot_row(row)]
        if decoded and is_business_date_token(decoded['date_dir'])
    ]


def _decode_snapshot_row(row) -> dict | None:
    if not row:
        return None
    return {
        'date_dir': row[0],
        'recommendations': json.loads(row[1] or '[]'),
        'briefing': json.loads(row[2] or '{}'),
        'sectors': json.loads(row[3] or '[]'),
        'stocks': json.loads(row[4] or '[]'),
    }


def _weekly_bucket(date_dir: str) -> str:
    dt = datetime.strptime(date_dir, '%Y%m%d')
    year, week, _ = dt.isocalendar()
    return f'{year}-W{week:02d}'


def _aggregate_sectors(rows: list[dict], limit: int) -> list[dict]:
    summary: dict[str, dict] = {}
    for row in rows:
        for rank, item in enumerate(row['sectors'], start=1):
            sector = item.get('sector', 'Unknown')
            bucket = summary.setdefault(
                sector,
                {
                    'sector': sector,
                    'appearance_count': 0,
                    'rank_total': 0,
                    'score_total': 0.0,
                    'ret_total': 0.0,
                    'alpha_total': 0,
                    'beta_total': 0,
                    'universe_count': 0,
                    'best_rank': rank,
                },
            )
            bucket['appearance_count'] += 1
            bucket['rank_total'] += rank
            bucket['score_total'] += float(item.get('leader_score', 0.0))
            bucket['ret_total'] += float(item.get('avg_ret120', 0.0))
            bucket['alpha_total'] += int(item.get('alpha_count', 0))
            bucket['beta_total'] += int(item.get('beta_count', 0))
            bucket['universe_count'] = max(bucket['universe_count'], int(item.get('universe_count', 0)))
            bucket['best_rank'] = min(bucket['best_rank'], rank)

    aggregated = []
    for item in summary.values():
        appearances = item['appearance_count']
        avg_rank = item['rank_total'] / appearances if appearances else 99.0
        avg_score = item['score_total'] / appearances if appearances else 0.0
        weekly_score = avg_score + appearances * 4.0 - avg_rank * 1.5
        aggregated.append(
            {
                'sector': item['sector'],
                'weekly_leader_score': round(weekly_score, 2),
                'avg_leader_score': round(avg_score, 2),
                'avg_ret120': round(item['ret_total'] / appearances, 4) if appearances else 0.0,
                'appearance_count': appearances,
                'best_rank': item['best_rank'],
                'alpha_count': item['alpha_total'],
                'beta_count': item['beta_total'],
                'universe_count': item['universe_count'],
            }
        )

    aggregated.sort(
        key=lambda item: (item['weekly_leader_score'], item['appearance_count'], -item['best_rank']),
        reverse=True,
    )
    return aggregated[:limit]


def _aggregate_stocks(rows: list[dict], limit: int) -> list[dict]:
    summary: dict[str, dict] = {}
    for row in rows:
        for rank, item in enumerate(row['stocks'], start=1):
            symbol = item.get('symbol', 'UNKNOWN')
            bucket = summary.setdefault(
                symbol,
                {
                    'symbol': symbol,
                    'name': item.get('name', symbol),
                    'sector': item.get('sector', 'Unknown'),
                    'appearance_count': 0,
                    'rank_total': 0,
                    'score_total': 0.0,
                    'alpha_total': 0.0,
                    'beta_total': 0.0,
                    'gamma_total': 0.0,
                    'ret_total': 0.0,
                    'best_rank': rank,
                },
            )
            bucket['appearance_count'] += 1
            bucket['rank_total'] += rank
            bucket['score_total'] += float(item.get('leader_stock_score', 0.0))
            bucket['alpha_total'] += float(item.get('alpha_score', 0.0))
            bucket['beta_total'] += float(item.get('beta_confidence', 0.0))
            bucket['gamma_total'] += float(item.get('gamma_score', 0.0))
            bucket['ret_total'] += float(item.get('ret120', 0.0))
            bucket['best_rank'] = min(bucket['best_rank'], rank)

    aggregated = []
    for item in summary.values():
        appearances = item['appearance_count']
        avg_rank = item['rank_total'] / appearances if appearances else 99.0
        avg_score = item['score_total'] / appearances if appearances else 0.0
        weekly_score = avg_score + appearances * 3.0 - avg_rank * 1.2
        aggregated.append(
            {
                'symbol': item['symbol'],
                'name': item['name'],
                'sector': item['sector'],
                'weekly_leader_score': round(weekly_score, 2),
                'avg_leader_stock_score': round(avg_score, 2),
                'appearance_count': appearances,
                'best_rank': item['best_rank'],
                'alpha_score': round(item['alpha_total'] / appearances, 2) if appearances else 0.0,
                'beta_confidence': round(item['beta_total'] / appearances, 2) if appearances else 0.0,
                'gamma_score': round(item['gamma_total'] / appearances, 2) if appearances else 0.0,
                'ret120': round(item['ret_total'] / appearances, 4) if appearances else 0.0,
            }
        )

    aggregated.sort(
        key=lambda item: (item['weekly_leader_score'], item['appearance_count'], -item['best_rank']),
        reverse=True,
    )
    return aggregated[:limit]
