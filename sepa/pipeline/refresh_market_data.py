from __future__ import annotations

import csv
import logging
import os
from datetime import datetime
from pathlib import Path

import yfinance as yf

from sepa.data.kiwoom import KiwoomProvider
from sepa.data.market_index import ensure_market_index_history
from sepa.data.quantdb import health as quantdb_health
from sepa.data.quantdb import read_price_rows as read_quantdb_price_rows
from sepa.data.symbols import infer_market, to_kiwoom_symbol
from sepa.data.universe import load_symbols
from sepa.pipeline.generate_sample_data import MIN_HISTORY_DAYS, ensure_min_history, generate_for_symbols

logger = logging.getLogger(__name__)


def _symbols() -> list[str]:
    return load_symbols()


def _has_any_csv(outdir: Path) -> bool:
    return any(outdir.glob('*.csv'))


def _fetch_yfinance_rows(symbol: str) -> list[dict]:
    try:
        frame = yf.download(symbol, period='8y', interval='1d', auto_adjust=False, progress=False)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        logger.warning('yfinance download failed for %s: %s', symbol, exc)
        return []
    if frame is None or frame.empty:
        return []
    if getattr(frame.columns, 'nlevels', 1) > 1:
        frame.columns = frame.columns.get_level_values(0)

    rows: list[dict] = []
    for idx, row in frame.iterrows():
        close = float(row.get('Close', 0.0) or 0.0)
        volume = int(float(row.get('Volume', 0.0) or 0.0))
        if close <= 0:
            continue
        rows.append(
            {
                'date': idx.date().isoformat(),
                'close': round(close, 2),
                'volume': max(0, volume),
            }
        )
    return rows


def _normalize_rows(rows: list[dict] | None) -> list[dict]:
    out: list[dict] = []
    for row in rows or []:
        date = str(row.get('date', '')).strip()
        try:
            close = float(row.get('close', 0.0) or 0.0)
            volume = int(float(row.get('volume', 0.0) or 0.0))
        except (TypeError, ValueError):
            continue
        if not date or close <= 0:
            continue
        out.append(
            {
                'date': date,
                'close': round(close, 2),
                'volume': max(0, volume),
            }
        )
    out.sort(key=lambda item: item['date'])
    return out


def _read_local_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open('r', encoding='utf-8', newline='') as handle:
        return _normalize_rows(list(csv.DictReader(handle)))


def _merge_rows(*sources: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for rows in sources:
        for row in _normalize_rows(rows):
            merged[row['date']] = row
    return [merged[key] for key in sorted(merged)]


def main() -> None:
    provider = KiwoomProvider()
    h = provider.health()
    print('[KIWOOM HEALTH]', h)
    print('[QUANTDB HEALTH]', quantdb_health())

    outdir = Path('data/market-data/ohlcv')
    symbols = _symbols()
    min_live_rows = max(252, int(os.getenv('SEPA_MIN_REAL_HISTORY_DAYS', str(MIN_HISTORY_DAYS)) or MIN_HISTORY_DAYS))
    updated = 0
    quantdb_updated = 0
    cached_updated = 0
    yf_updated = 0
    missing: list[str] = []
    today_token = datetime.now().date().isoformat()
    force_live_refresh = os.getenv('SEPA_FORCE_LIVE_REFRESH', '0').strip() == '1'

    for sym in symbols:
        code = to_kiwoom_symbol(sym)
        market = infer_market(sym)
        print(f'[TRY] {sym} -> code={code}, market={market}')
        local_rows = _read_local_rows(outdir / f'{sym}.csv')
        quantdb_rows = read_quantdb_price_rows(sym)
        cached_rows = _merge_rows(local_rows, quantdb_rows)
        if (
            cached_rows
            and not force_live_refresh
            and len(cached_rows) >= min_live_rows
            and cached_rows[-1]['date'] >= today_token
        ):
            cached_updated += 1
            print(f'[CACHE] {sym}: {len(cached_rows)} rows already current')
            continue

        if len(quantdb_rows) >= min_live_rows:
            generate_for_symbols([sym], source_rows={sym: quantdb_rows}, overwrite=True)
            quantdb_updated += 1
            print(f'[DB] {sym}: {len(quantdb_rows)} rows updated from QuantDB')
            continue

        kiwoom_rows = provider.fetch_ohlcv(sym, limit=min_live_rows)

        # Merge: QuantDB + Kiwoom only (no Yahoo Finance)
        live_rows = _merge_rows(quantdb_rows, [], kiwoom_rows)
        if live_rows:
            generate_for_symbols([sym], source_rows={sym: live_rows}, overwrite=True)
            if quantdb_rows:
                quantdb_updated += 1
            if kiwoom_rows:
                updated += 1
            source_bits = []
            if quantdb_rows:
                source_bits.append(f'quantdb={len(quantdb_rows)}')
            if kiwoom_rows:
                source_bits.append(f'kiwoom={len(kiwoom_rows)}')
            source_label = ', '.join(source_bits) if source_bits else 'live'
            print(f'[LIVE] {sym}: {len(live_rows)} merged rows ({source_label})')
            continue

        if not live_rows:
            if (outdir / f'{sym}.csv').exists():
                print(f'[KEEP] using local csv for {sym}')
                continue
            print(f'[MISS] no live data for {sym}')
            missing.append(sym)
            continue

    generated = generate_for_symbols(missing, overwrite=False) if missing else []
    if generated:
        print(f'[FALLBACK] generated sample data for {len(generated)} symbols')

    if updated == 0 and not _has_any_csv(outdir):
        print('[FALLBACK] no live data and no local csv -> generating full sample universe')
        generated = generate_for_symbols(symbols, overwrite=False, min_length=MIN_HISTORY_DAYS)
        if generated:
            print(f'[FALLBACK] generated sample data for {len(generated)} symbols')

    extended = ensure_min_history(symbols, min_length=MIN_HISTORY_DAYS)
    if extended:
        print(f'[HISTORY] extended local/sample history for {len(extended)} symbols to {MIN_HISTORY_DAYS} business days')

    index_updated = ensure_market_index_history(['KOSPI', 'KOSDAQ'])
    if index_updated:
        for market, count in index_updated.items():
            print(f'[INDEX] {market}: {count} rows updated')
    else:
        print('[INDEX] market benchmark fetch skipped; keeping local index csv if present')

    # Sync CSV data to SQLite for fast batch queries
    try:
        from sepa.data.ohlcv_db import sync_from_csv_dir
        synced = sync_from_csv_dir(outdir)
        print(f'[DB] synced {synced:,} rows to ohlcv.db')
    except Exception as exc:
        print(f'[DB] sync skipped: {exc}')

    print(
        f'[DONE] refreshed symbols: cache={cached_updated} quantdb={quantdb_updated} '
        f'live={updated} yfinance={yf_updated} sample={len(generated)} total_universe={len(symbols)}'
    )


if __name__ == '__main__':
    main()
