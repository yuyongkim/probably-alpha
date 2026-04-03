"""Fetch fundamental data (PER/EPS/ROE/PBR/BPS/revenue/op_profit/net_income)
from Kiwoom REST API (ka10001) for all stocks in ohlcv.db and persist results.

Usage:
    python scripts/fetch_kiwoom_financials.py
"""
from __future__ import annotations

import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Load .env manually (no external dependency)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / '.env'

def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

_load_env(ENV_PATH)

# ---------------------------------------------------------------------------
# Imports from project
# ---------------------------------------------------------------------------
sys.path.insert(0, str(PROJECT_ROOT))

from sepa.data.kiwoom import KiwoomProvider  # noqa: E402
from sepa.data.symbols import to_kiwoom_symbol  # noqa: E402

DB_PATH = PROJECT_ROOT / '.omx' / 'artifacts' / 'ohlcv.db'

# Financial columns to add to symbol_meta (if they don't exist yet)
FINANCIAL_COLS = ['per', 'eps', 'roe', 'pbr', 'bps', 'revenue', 'op_profit', 'net_income']


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA busy_timeout=30000')
    return conn


def _ensure_columns(conn: sqlite3.Connection) -> None:
    """Add financial columns to symbol_meta if they don't already exist."""
    existing = {row[1] for row in conn.execute('PRAGMA table_info(symbol_meta)').fetchall()}
    for col in FINANCIAL_COLS:
        if col not in existing:
            col_type = 'REAL'
            conn.execute(f'ALTER TABLE symbol_meta ADD COLUMN {col} {col_type}')
            print(f'  Added column symbol_meta.{col}')
    conn.commit()


def _ensure_financials_table(conn: sqlite3.Connection) -> None:
    """Create financials table if it doesn't exist."""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS financials (
            symbol      TEXT NOT NULL,
            period      TEXT NOT NULL,
            period_type TEXT NOT NULL,
            metric      TEXT NOT NULL,
            value       REAL,
            PRIMARY KEY (symbol, period, metric)
        )
    ''')
    conn.commit()


def _get_all_symbols(conn: sqlite3.Connection) -> list[str]:
    """Get all symbols from symbol_meta."""
    rows = conn.execute('SELECT symbol FROM symbol_meta ORDER BY symbol').fetchall()
    return [row['symbol'] for row in rows]


def _update_symbol_meta(conn: sqlite3.Connection, symbol: str, info: dict) -> None:
    """Update symbol_meta row with financial snapshot data."""
    sets = []
    vals = []
    for col in FINANCIAL_COLS:
        if col in info:
            sets.append(f'{col} = ?')
            vals.append(info[col])
    if not sets:
        return
    vals.append(symbol)
    conn.execute(
        f'UPDATE symbol_meta SET {", ".join(sets)} WHERE symbol = ?',
        vals,
    )


def _insert_financials(conn: sqlite3.Connection, symbol: str, info: dict, period: str) -> None:
    """Insert rows into financials table (one row per metric)."""
    code = to_kiwoom_symbol(symbol)
    metric_map = {
        'revenue': '매출액',
        'op_profit': '영업이익',
        'net_income': '당기순이익',
        'eps': 'EPS',
        'bps': 'BPS',
        'per': 'PER',
        'pbr': 'PBR',
        'roe': 'ROE',
    }
    for key, metric_name in metric_map.items():
        val = info.get(key)
        if val is None:
            continue
        conn.execute(
            'INSERT OR REPLACE INTO financials (symbol, period, period_type, metric, value) VALUES (?, ?, ?, ?, ?)',
            (code, period, 'annual', metric_name, val),
        )


def main() -> None:
    if not DB_PATH.exists():
        print(f'ERROR: Database not found at {DB_PATH}')
        sys.exit(1)

    conn = _connect()
    _ensure_columns(conn)
    _ensure_financials_table(conn)

    symbols = _get_all_symbols(conn)
    total = len(symbols)
    print(f'Found {total} symbols in symbol_meta')
    print(f'Estimated time: {total * 0.25 / 60:.1f} minutes')
    print()

    provider = KiwoomProvider()
    health = provider.health()
    if not health['has_app_key'] or not health['has_secret_key']:
        print('ERROR: KIWOOM_APP_KEY or KIWOOM_SECRET_KEY not set in .env')
        sys.exit(1)
    print(f'Kiwoom health: {health}')
    print()

    current_year = str(datetime.now().year)
    success_count = 0
    skip_count = 0
    error_count = 0
    start_time = time.time()

    for i, symbol in enumerate(symbols):
        info = provider.fetch_stock_info(symbol)

        if not info:
            skip_count += 1
        else:
            _update_symbol_meta(conn, symbol, info)
            _insert_financials(conn, symbol, info, current_year)
            success_count += 1

        # Commit every 100 stocks
        if (i + 1) % 100 == 0:
            conn.commit()
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (total - i - 1) / rate if rate > 0 else 0
            print(
                f'  [{i + 1}/{total}] '
                f'ok={success_count} skip={skip_count} err={error_count} '
                f'elapsed={elapsed:.0f}s remaining~{remaining:.0f}s'
            )

        # Rate limit: ~2 calls/sec (conservative to avoid IP ban)
        time.sleep(0.5)

    conn.commit()
    conn.close()

    elapsed = time.time() - start_time
    print()
    print(f'Done in {elapsed:.0f}s')
    print(f'  Success: {success_count}')
    print(f'  Skipped: {skip_count}')
    print(f'  Errors:  {error_count}')


if __name__ == '__main__':
    main()
