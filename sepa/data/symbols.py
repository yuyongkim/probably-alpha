from __future__ import annotations


def to_kiwoom_symbol(symbol: str) -> str:
    """005930.KS -> 005930, A005930 -> 005930"""
    s = symbol.strip().upper()
    if s.startswith('A') and len(s) >= 7 and s[1:7].isdigit():
        return s[1:7]
    if '.' in s:
        left = s.split('.', 1)[0]
        if left.isdigit():
            return left
    return s


def infer_market(symbol: str, default_market: str = 'KOSPI') -> str:
    s = symbol.strip().upper()
    if s.endswith('.KQ'):
        return 'KOSDAQ'
    if s.endswith('.KS'):
        return 'KOSPI'
    return default_market
