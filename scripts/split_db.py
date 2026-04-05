"""Split sepa.db into 4 purpose-specific databases.

data/ohlcv.db      ← 시세 (키움)
data/meta.db       ← 종목 메타 + 수집 로그
data/financial.db  ← 재무 (네이버)
data/market.db     ← 섹터비교 + 수급
"""
import os
import sqlite3
import sys

SRC = 'data/sepa.db'

SPLITS = {
    'data/ohlcv.db': {
        'ohlcv': """
            CREATE TABLE IF NOT EXISTS ohlcv (
                symbol     TEXT    NOT NULL,
                trade_date TEXT    NOT NULL,
                close      REAL   NOT NULL,
                volume     INTEGER DEFAULT 0,
                PRIMARY KEY (symbol, trade_date)
            )""",
    },
    'data/meta.db': {
        'symbol_meta': """
            CREATE TABLE IF NOT EXISTS symbol_meta (
                symbol              TEXT PRIMARY KEY NOT NULL,
                name                TEXT,
                sector              TEXT,
                industry            TEXT,
                last_updated        TEXT,
                per                 REAL,
                eps                 REAL,
                roe                 REAL,
                pbr                 REAL,
                bps                 REAL,
                revenue             REAL,
                op_profit           REAL,
                net_income          REAL,
                market_cap          TEXT,
                foreign_ratio       TEXT,
                high_52w            TEXT,
                low_52w             TEXT,
                consensus_target    TEXT,
                consensus_opinion   REAL,
                est_per             TEXT,
                est_eps             TEXT,
                dividend_yield      TEXT,
                description         TEXT,
                shares_outstanding_calc REAL,
                market_cap_krw      REAL
            )""",
        'dart_corp_code': """
            CREATE TABLE IF NOT EXISTS dart_corp_code (
                stock_code TEXT PRIMARY KEY NOT NULL,
                corp_code  TEXT NOT NULL,
                corp_name  TEXT
            )""",
        'fetch_log': """
            CREATE TABLE IF NOT EXISTS fetch_log (
                symbol     TEXT NOT NULL,
                source     TEXT NOT NULL,
                status     TEXT NOT NULL,
                fetched_at TEXT NOT NULL,
                error_msg  TEXT,
                rows_saved INTEGER DEFAULT 0,
                PRIMARY KEY (symbol, source)
            )""",
    },
    'data/financial.db': {
        'financial_snapshot': """
            CREATE TABLE IF NOT EXISTS financial_snapshot (
                symbol          TEXT PRIMARY KEY NOT NULL,
                price           REAL,
                market_cap_krw  REAL,
                shares_outstanding REAL,
                per             REAL,
                eps             REAL,
                pbr             REAL,
                bps             REAL,
                roe             REAL,
                cns_per         REAL,
                cns_eps         REAL,
                target_price    REAL,
                recommend_score REAL,
                dividend_yield  REAL,
                dividend        REAL,
                foreign_ratio   REAL,
                high_52w        REAL,
                low_52w         REAL,
                updated_at      TEXT,
                source          TEXT DEFAULT 'naver_mobile'
            )""",
        'financials': """
            CREATE TABLE IF NOT EXISTS financials (
                symbol      TEXT NOT NULL,
                period      TEXT NOT NULL,
                period_type TEXT NOT NULL,
                metric      TEXT NOT NULL,
                value       REAL,
                PRIMARY KEY (symbol, period, metric)
            )""",
        'financial_statements': """
            CREATE TABLE IF NOT EXISTS financial_statements (
                symbol         TEXT    NOT NULL,
                period         TEXT    NOT NULL,
                period_type    TEXT    NOT NULL,
                account_code   TEXT,
                account_name   TEXT    NOT NULL,
                account_level  INTEGER,
                value          REAL,
                yoy            REAL,
                is_estimate    INTEGER DEFAULT 0,
                source         TEXT    DEFAULT 'naver_comp',
                PRIMARY KEY (symbol, period, account_name)
            )""",
        'financial_metrics': """
            CREATE TABLE IF NOT EXISTS financial_metrics (
                symbol  TEXT NOT NULL,
                period  TEXT NOT NULL,
                metric  TEXT NOT NULL,
                value   REAL,
                source  TEXT DEFAULT 'naver_comp',
                PRIMARY KEY (symbol, period, metric)
            )""",
    },
    'data/market.db': {
        'sector_comparison': """
            CREATE TABLE IF NOT EXISTS sector_comparison (
                symbol         TEXT NOT NULL,
                metric         TEXT NOT NULL,
                company_value  REAL,
                sector_value   REAL,
                market_value   REAL,
                period         TEXT,
                updated_at     TEXT,
                PRIMARY KEY (symbol, metric)
            )""",
        'investor_trend': """
            CREATE TABLE IF NOT EXISTS investor_trend (
                symbol         TEXT    NOT NULL,
                trade_date     TEXT    NOT NULL,
                foreign_net    INTEGER,
                foreign_ratio  REAL,
                institution_net INTEGER,
                individual_net INTEGER,
                close_price    REAL,
                volume         INTEGER,
                PRIMARY KEY (symbol, trade_date)
            )""",
    },
}

INDEXES = {
    'data/ohlcv.db': [
        'CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol ON ohlcv(symbol)',
        'CREATE INDEX IF NOT EXISTS idx_ohlcv_date ON ohlcv(trade_date)',
    ],
    'data/financial.db': [
        'CREATE INDEX IF NOT EXISTS idx_fin_symbol ON financials(symbol)',
        'CREATE INDEX IF NOT EXISTS idx_finstmt_symbol ON financial_statements(symbol)',
        'CREATE INDEX IF NOT EXISTS idx_finstmt_period ON financial_statements(period)',
        'CREATE INDEX IF NOT EXISTS idx_finmet_symbol ON financial_metrics(symbol)',
    ],
    'data/market.db': [
        'CREATE INDEX IF NOT EXISTS idx_trend_symbol ON investor_trend(symbol)',
    ],
}


def main():
    if not os.path.exists(SRC):
        print(f'Source not found: {SRC}')
        sys.exit(1)

    src = sqlite3.connect(SRC)
    src.row_factory = sqlite3.Row

    for db_path, tables in SPLITS.items():
        print(f'\n=== {db_path} ===', flush=True)
        dst = sqlite3.connect(db_path)
        dst.execute('PRAGMA journal_mode=DELETE')
        dst.execute('PRAGMA synchronous=NORMAL')

        for table_name, create_sql in tables.items():
            dst.execute(create_sql)

            # Get column info from source
            cols_info = src.execute(f'PRAGMA table_info({table_name})').fetchall()
            cols = [c[1] for c in cols_info]
            placeholders = ','.join(['?'] * len(cols))
            col_names = ','.join(cols)

            # Copy in batches
            total = src.execute(f'SELECT count(*) FROM {table_name}').fetchone()[0]
            if total == 0:
                print(f'  {table_name}: 0 rows', flush=True)
                continue

            batch_size = 50000
            copied = 0
            cursor = src.execute(f'SELECT {col_names} FROM {table_name}')
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                dst.executemany(
                    f'INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})',
                    [tuple(r) for r in rows],
                )
                copied += len(rows)
                if copied % 100000 == 0 or copied == total:
                    print(f'  {table_name}: {copied:>12,} / {total:,}', flush=True)

            dst.commit()
            print(f'  {table_name}: {copied:>12,} rows  DONE', flush=True)

        # Create indexes
        for idx_sql in INDEXES.get(db_path, []):
            dst.execute(idx_sql)
        dst.commit()
        dst.close()

    src.close()

    # Report sizes
    print('\n=== Result ===')
    total_new = 0
    for f in ['data/ohlcv.db', 'data/meta.db', 'data/financial.db', 'data/market.db', 'data/recommendations.db']:
        if os.path.exists(f):
            sz = os.path.getsize(f)
            total_new += sz
            print(f'  {f:30s} {sz/1024/1024:>8.1f} MB')
    print(f'  {"TOTAL (new)":30s} {total_new/1024/1024:>8.1f} MB')
    print(f'  {"data/sepa.db (old)":30s} {os.path.getsize(SRC)/1024/1024:>8.1f} MB')


if __name__ == '__main__':
    main()
