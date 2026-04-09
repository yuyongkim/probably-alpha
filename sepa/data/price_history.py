from __future__ import annotations

import csv
from bisect import bisect_left, bisect_right
from functools import lru_cache
from datetime import date, datetime, timedelta
from pathlib import Path


def normalize_date_token(value: str | None) -> str:
    raw = str(value or '').strip()
    if not raw:
        return ''
    digits = ''.join(ch for ch in raw if ch.isdigit())
    if len(digits) == 8:
        return digits
    return raw.replace('-', '')


def format_date_token(value: str | None) -> str:
    token = normalize_date_token(value)
    if len(token) == 8 and token.isdigit():
        try:
            datetime.strptime(token, '%Y%m%d')
        except ValueError:
            return token
        return f'{token[:4]}-{token[4:6]}-{token[6:8]}'
    return token


def is_business_date_token(value: str | None) -> bool:
    token = normalize_date_token(value)
    if len(token) != 8 or not token.isdigit():
        return False
    try:
        return datetime.strptime(token, '%Y%m%d').weekday() < 5
    except ValueError:
        return False


# ── KRX 공휴일 (주말 제외, 고정+변동) ──
# 매년 업데이트 필요. 음력 기반 공휴일은 연도별 하드코딩.
_KRX_HOLIDAYS: set[str] = {
    # 2025
    '20250101', '20250128', '20250129', '20250130',  # 신정, 설날
    '20250301', '20250505', '20250506',               # 삼일절, 어린이날, 대체
    '20250601', '20250606', '20250815',               # 석가탄신일, 현충일, 광복절
    '20251003', '20251005', '20251006', '20251007',   # 개천절, 추석
    '20251009', '20251225',                            # 한글날, 성탄절
    # 2026
    '20260101', '20260216', '20260217', '20260218',   # 신정, 설날
    '20260301', '20260505', '20260519',               # 삼일절, 어린이날, 석가탄신일
    '20260606', '20260815',                            # 현충일, 광복절
    '20260924', '20260925', '20260926',               # 추석
    '20261003', '20261009', '20261225',               # 개천절, 한글날, 성탄절
    # 2027
    '20270101', '20270205', '20270206', '20270207',   # 신정, 설날
    '20270301', '20270505', '20270513',               # 삼일절, 어린이날, 석가탄신일
    '20270606', '20270815',                            # 현충일, 광복절
    '20271003', '20271009', '20271013', '20271014', '20271015',  # 개천절, 한글날, 추석
    '20271225',                                        # 성탄절
}


def is_krx_trading_day(d: date) -> bool:
    """주말과 KRX 공휴일을 모두 체크하여 실제 거래일인지 판단."""
    if d.weekday() >= 5:
        return False
    return d.strftime('%Y%m%d') not in _KRX_HOLIDAYS


def previous_trading_date(ref: date | None = None) -> str:
    """ref 기준 직전 거래일(영업일)을 YYYYMMDD 형식으로 반환.

    ref가 None이면 오늘 기준.
    ref 자체가 거래일이면 ref의 전 거래일을 반환.
    """
    cursor = (ref or date.today()) - timedelta(days=1)
    while not is_krx_trading_day(cursor):
        cursor -= timedelta(days=1)
    return cursor.strftime('%Y%m%d')


def latest_trading_date(ref: date | None = None) -> str:
    """ref 기준 가장 최근 거래일을 YYYYMMDD 형식으로 반환.

    ref가 거래일이면 ref를 반환. 아니면 직전 거래일.
    ref가 None이면 오늘 기준.
    """
    cursor = ref or date.today()
    while not is_krx_trading_day(cursor):
        cursor -= timedelta(days=1)
    return cursor.strftime('%Y%m%d')


def read_price_series(
    symbol: str,
    data_dir: Path = Path('data/market-data/ohlcv'),
    as_of_date: str | None = None,
) -> list[dict]:
    path = data_dir / f'{symbol}.csv'
    return read_price_series_from_path(path, as_of_date=as_of_date)


def read_price_series_from_path(path: Path, as_of_date: str | None = None) -> list[dict]:
    # Try SQLite first (fast path)
    try:
        from sepa.data.ohlcv_db import read_ohlcv, DB_PATH
        if DB_PATH.exists():
            symbol = path.stem
            rows = read_ohlcv(symbol, as_of_date=as_of_date)
            if rows:
                return rows
    except Exception:
        pass

    # Fallback to CSV
    cutoff = normalize_date_token(as_of_date)
    rows = _read_price_rows_cached(str(path), _path_mtime_ns(path))
    if not cutoff:
        return [{'date': item[1], 'close': item[2], 'volume': item[3]} for item in rows]
    return [
        {'date': item[1], 'close': item[2], 'volume': item[3]}
        for item in rows
        if not item[0] or item[0] <= cutoff
    ]


def available_dates(data_dir: Path = Path('data/market-data/ohlcv')) -> list[str]:
    return list(_available_dates_fast(str(data_dir), _data_dir_file_count(data_dir)))


def nearest_available_date(value: str | None, data_dir: Path = Path('data/market-data/ohlcv')) -> str:
    dates = available_dates(data_dir)
    if not dates:
        return ''
    token = normalize_date_token(value)
    if not token:
        return dates[-1]
    pos = bisect_right(dates, token)
    if pos <= 0:
        return dates[0]
    return dates[pos - 1]


def trailing_available_dates(
    end_token: str | None = None,
    length: int = 126,
    data_dir: Path = Path('data/market-data/ohlcv'),
) -> list[str]:
    dates = available_dates(data_dir)
    if not dates or length <= 0:
        return []
    resolved = nearest_available_date(end_token, data_dir=data_dir)
    if not resolved:
        return []
    end_index = bisect_right(dates, resolved)
    start_index = max(0, end_index - length)
    return dates[start_index:end_index]


def leading_available_dates(
    start_token: str | None,
    length: int = 126,
    data_dir: Path = Path('data/market-data/ohlcv'),
) -> list[str]:
    dates = available_dates(data_dir)
    if not dates or length <= 0:
        return []
    resolved = nearest_available_date(start_token, data_dir=data_dir)
    if not resolved:
        return []
    start_index = bisect_left(dates, resolved)
    return dates[start_index:start_index + length]


def _path_mtime_ns(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


def _data_dir_file_count(data_dir: Path) -> int:
    """Lightweight cache-bust key: file count + latest mtime.
    This invalidates the cache when files are added/removed OR updated."""
    if not data_dir.exists():
        return 0
    count = 0
    max_mtime = 0
    for p in data_dir.glob('*.csv'):
        count += 1
        try:
            mt = int(p.stat().st_mtime)
        except OSError:
            continue
        if mt > max_mtime:
            max_mtime = mt
    return count * 1_000_000 + (max_mtime % 1_000_000)


@lru_cache(maxsize=8)
def _available_dates_fast(data_dir_str: str, file_count: int) -> tuple[str, ...]:
    """Extract trading dates from the largest CSV file instead of reading
    all 2000+ files.  All KRX-listed symbols share the same trading
    calendar, so one representative file is sufficient."""
    data_dir = Path(data_dir_str)
    if not data_dir.exists():
        return ()

    # Sample several large CSVs and merge their dates to avoid missing
    # recent dates when some files were extended backward by ensure_min_history.
    candidates: list[tuple[float, Path]] = []
    for path in data_dir.glob('*.csv'):
        try:
            stat = path.stat()
        except OSError:
            continue
        candidates.append((stat.st_size, path))

    if not candidates:
        return ()

    # Take top-10 by size — enough to cover any stale outliers
    candidates.sort(key=lambda t: t[0], reverse=True)
    sample = candidates[:10]

    dates: set[str] = set()
    for _size, path in sample:
        rows = _read_price_rows_cached(str(path), _path_mtime_ns(path))
        for token, _formatted, _close, _volume in rows:
            if token:
                dates.add(token)
    return tuple(sorted(dates))


def _data_dir_signature(data_dir: Path) -> tuple[tuple[str, int], ...]:
    if not data_dir.exists():
        return ()
    return tuple(
        sorted(
            (path.name, _path_mtime_ns(path))
            for path in data_dir.glob('*.csv')
        )
    )


@lru_cache(maxsize=1024)
def _read_price_rows_cached(path_str: str, mtime_ns: int) -> tuple[tuple[str, str, float, float], ...]:
    path = Path(path_str)
    if not path.exists():
        return ()

    raw_rows: list[dict] = []
    with path.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_rows.append(row)

    date_tokens = [normalize_date_token(row.get('date')) for row in raw_rows]
    if raw_rows and not any(date_tokens):
        fallback_tokens = _legacy_date_tokens(path.parent, len(raw_rows))
        date_tokens = fallback_tokens[-len(raw_rows) :]

    out: list[tuple[str, str, float, float]] = []
    for row, date_token in zip(raw_rows, date_tokens, strict=False):
        if date_token and not is_business_date_token(date_token):
            continue
        close = _to_num(row.get('close'))
        if close <= 0:
            continue
        out.append(
            (
                date_token,
                format_date_token(date_token),
                close,
                _to_num(row.get('volume')),
            )
        )
    return tuple(out)


@lru_cache(maxsize=8)
def _available_dates_cached(data_dir_str: str, signature: tuple[tuple[str, int], ...]) -> tuple[str, ...]:
    data_dir = Path(data_dir_str)
    dates: set[str] = set()
    for name, mtime_ns in signature:
        for token, _formatted, _close, _volume in _read_price_rows_cached(str(data_dir / name), mtime_ns):
            if token:
                dates.add(token)
    return tuple(sorted(dates))


@lru_cache(maxsize=8)
def _legacy_date_tokens(data_dir: Path, length: int) -> list[str]:
    dates = available_dates(data_dir)
    if len(dates) >= length:
        return dates[-length:]
    end_token = dates[-1] if dates else date.today().strftime('%Y%m%d')
    return _business_day_series(length=length, end_token=end_token)


def _business_day_series(length: int, end_token: str) -> list[str]:
    cursor = datetime.strptime(end_token, '%Y%m%d').date()
    out: list[str] = []
    while len(out) < length:
        if cursor.weekday() < 5:
            out.append(cursor.strftime('%Y%m%d'))
        cursor -= timedelta(days=1)
    out.reverse()
    return out


def _to_num(value) -> float:
    try:
        return float(str(value).replace(',', ''))
    except Exception:
        return 0.0
