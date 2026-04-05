"""OHLCV SQLite database — replaces 2700+ CSV file reads with indexed queries.

DB path: data/ohlcv.db
Schema: ohlcv(symbol, trade_date, close, volume) with composite PK.
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

DB_PATH = Path('data/ohlcv.db')
META_DB_PATH = Path('data/meta.db')

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ohlcv (
    symbol     TEXT    NOT NULL,
    trade_date TEXT    NOT NULL,
    close      REAL    NOT NULL,
    volume     INTEGER DEFAULT 0,
    PRIMARY KEY (symbol, trade_date)
);
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol ON ohlcv(symbol);
CREATE INDEX IF NOT EXISTS idx_ohlcv_date   ON ohlcv(trade_date);
"""


def _connect(path: Path | None = None) -> sqlite3.Connection:
    p = path or DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=DELETE')
    conn.execute('PRAGMA synchronous=NORMAL')
    return conn


def ensure_db(path: Path | None = None) -> Path:
    """Create DB and schema if not exists. Returns DB path."""
    p = path or DB_PATH
    conn = _connect(p)
    conn.executescript(_SCHEMA)
    conn.close()
    return p


def import_csv_dir(csv_dir: Path, db_path: Path | None = None, *, verbose: bool = False) -> int:
    """Bulk import all CSVs from a directory into the DB. Returns row count."""
    ensure_db(db_path)
    conn = _connect(db_path)
    total = 0
    csv_files = sorted(csv_dir.glob('*.csv'))

    for i, path in enumerate(csv_files):
        symbol = path.stem
        rows = _parse_csv(path)
        if not rows:
            continue
        conn.executemany(
            'INSERT OR REPLACE INTO ohlcv (symbol, trade_date, close, volume) VALUES (?, ?, ?, ?)',
            [(symbol, r['date'], r['close'], r['volume']) for r in rows],
        )
        total += len(rows)
        if verbose and (i + 1) % 500 == 0:
            print(f'  imported {i + 1}/{len(csv_files)} files ({total:,} rows)')

    conn.commit()
    conn.close()
    return total


def read_ohlcv(symbol: str, *, as_of_date: str | None = None, db_path: Path | None = None) -> list[dict]:
    """Read OHLCV for a single symbol. Returns [{date, close, volume}, ...]."""
    p = db_path or DB_PATH
    if not p.exists():
        return []
    sym = _bare(symbol)
    conn = _connect(p)
    try:
        if as_of_date:
            cutoff = as_of_date.replace('-', '')
            rows = conn.execute(
                'SELECT trade_date, close, volume FROM ohlcv WHERE symbol = ? AND trade_date <= ? ORDER BY trade_date',
                (sym, cutoff),
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT trade_date, close, volume FROM ohlcv WHERE symbol = ? ORDER BY trade_date',
                (sym,),
            ).fetchall()
    finally:
        conn.close()

    return [
        {
            'date': _format_date(row['trade_date']),
            'close': float(row['close']),
            'volume': int(row['volume']),
        }
        for row in rows
        if float(row['close']) > 0
    ]


def read_ohlcv_batch(
    symbols: list[str] | None = None,
    *,
    as_of_date: str | None = None,
    min_rows: int = 50,
    db_path: Path | None = None,
) -> dict[str, dict]:
    """Batch read OHLCV for many symbols at once. Returns {symbol: {closes, volumes}}.

    This is the key performance optimization — one SQL query instead of 2716 file reads.
    """
    p = db_path or DB_PATH
    if not p.exists():
        return {}
    conn = _connect(p)
    try:
        if symbols:
            placeholders = ','.join('?' * len(symbols))
            if as_of_date:
                cutoff = as_of_date.replace('-', '')
                query = f'SELECT symbol, trade_date, close, volume FROM ohlcv WHERE symbol IN ({placeholders}) AND trade_date <= ? ORDER BY symbol, trade_date'
                rows = conn.execute(query, [*symbols, cutoff]).fetchall()
            else:
                query = f'SELECT symbol, trade_date, close, volume FROM ohlcv WHERE symbol IN ({placeholders}) ORDER BY symbol, trade_date'
                rows = conn.execute(query, symbols).fetchall()
        else:
            if as_of_date:
                cutoff = as_of_date.replace('-', '')
                rows = conn.execute(
                    'SELECT symbol, trade_date, close, volume FROM ohlcv WHERE trade_date <= ? ORDER BY symbol, trade_date',
                    (cutoff,),
                ).fetchall()
            else:
                rows = conn.execute('SELECT symbol, trade_date, close, volume FROM ohlcv ORDER BY symbol, trade_date').fetchall()
    finally:
        conn.close()

    result: dict[str, dict] = {}
    for row in rows:
        sym = row['symbol']
        close = float(row['close'])
        if close <= 0:
            continue
        if sym not in result:
            result[sym] = {'closes': [], 'volumes': []}
        result[sym]['closes'].append(close)
        result[sym]['volumes'].append(int(row['volume']))

    # Filter by min_rows
    if min_rows > 0:
        result = {k: v for k, v in result.items() if len(v['closes']) >= min_rows}

    return result


def upsert_rows(symbol: str, rows: list[dict], *, db_path: Path | None = None) -> int:
    """Insert or update rows for a symbol. Returns count."""
    if not rows:
        return 0
    ensure_db(db_path)
    conn = _connect(db_path)
    data = [
        (symbol, str(r.get('date', '')).replace('-', ''), float(r.get('close', 0)), int(float(r.get('volume', 0))))
        for r in rows
        if float(r.get('close', 0)) > 0
    ]
    conn.executemany(
        'INSERT OR REPLACE INTO ohlcv (symbol, trade_date, close, volume) VALUES (?, ?, ?, ?)',
        data,
    )
    conn.commit()
    conn.close()
    return len(data)


def get_all_symbols(*, db_path: Path | None = None) -> list[str]:
    """Return all symbols in the DB."""
    p = db_path or DB_PATH
    if not p.exists():
        return []
    conn = _connect(p)
    try:
        rows = conn.execute('SELECT DISTINCT symbol FROM ohlcv ORDER BY symbol').fetchall()
    finally:
        conn.close()
    return [row['symbol'] for row in rows]


def _bare(symbol: str) -> str:
    """Strip .KS/.KQ suffix — DB stores bare codes only."""
    return symbol.replace('.KS', '').replace('.KQ', '')


def get_symbol_name_from_db(symbol: str, *, db_path: Path | None = None) -> str:
    """Get stock name from symbol_meta table (meta.db)."""
    p = db_path or META_DB_PATH
    if not p.exists():
        return ''
    conn = _connect(p)
    try:
        row = conn.execute('SELECT name FROM symbol_meta WHERE symbol = ?', (_bare(symbol),)).fetchone()
    except Exception:
        return ''
    finally:
        conn.close()
    return row['name'] if row else ''


def get_symbol_meta(symbol: str, *, db_path: Path | None = None) -> dict:
    """Get full metadata (name, sector, industry) from meta.db."""
    p = db_path or META_DB_PATH
    if not p.exists():
        return {}
    conn = _connect(p)
    try:
        row = conn.execute('SELECT * FROM symbol_meta WHERE symbol = ?', (_bare(symbol),)).fetchone()
    except Exception:
        return {}
    finally:
        conn.close()
    return dict(row) if row else {}


def get_active_universe(*, min_date: str = '20260301', min_rows: int = 200, db_path: Path | None = None) -> list[dict]:
    """Get actively traded symbols with metadata.

    Uses ATTACH to join ohlcv.db and meta.db.
    """
    p = db_path or DB_PATH
    if not p.exists():
        return []
    conn = _connect(p)
    try:
        conn.execute(f"ATTACH DATABASE '{META_DB_PATH}' AS meta_db")
        rows = conn.execute('''
            SELECT o.symbol, m.name, m.sector, m.industry,
                   COUNT(*) as row_count, MAX(o.trade_date) as last_date
            FROM ohlcv o
            LEFT JOIN meta_db.symbol_meta m ON o.symbol = m.symbol
            WHERE o.symbol NOT LIKE '9%'
            GROUP BY o.symbol
            HAVING MAX(o.trade_date) >= ? AND COUNT(*) >= ?
            ORDER BY o.symbol
        ''', (min_date, min_rows)).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def sync_from_csv_dir(csv_dir: Path, *, db_path: Path | None = None) -> int:
    """Sync DB from CSV directory — only imports symbols not yet in DB or with newer data."""
    ensure_db(db_path)
    existing = set(get_all_symbols(db_path=db_path))
    conn = _connect(db_path)
    total = 0
    for path in sorted(csv_dir.glob('*.csv')):
        symbol = path.stem
        rows = _parse_csv(path)
        if not rows:
            continue
        conn.executemany(
            'INSERT OR REPLACE INTO ohlcv (symbol, trade_date, close, volume) VALUES (?, ?, ?, ?)',
            [(symbol, r['date'], r['close'], r['volume']) for r in rows],
        )
        total += len(rows)
    conn.commit()
    conn.close()
    return total


def _parse_csv(path: Path) -> list[dict]:
    """Parse a single CSV file into row dicts."""
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open('r', encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            date_str = str(row.get('date', '')).strip().replace('-', '')
            try:
                close = float(row.get('close', 0) or 0)
                volume = int(float(row.get('volume', 0) or 0))
            except (ValueError, TypeError):
                continue
            if date_str and close > 0:
                rows.append({'date': date_str, 'close': round(close, 2), 'volume': max(0, volume)})
    return rows


def _format_date(token: str) -> str:
    """YYYYMMDD -> YYYY-MM-DD"""
    t = token.replace('-', '')
    if len(t) == 8 and t.isdigit():
        return f'{t[:4]}-{t[4:6]}-{t[6:8]}'
    return token
