"""Piotroski F-Score (9 binary signals)."""
from __future__ import annotations

from typing import Any

from ky_core.quant.pit import fin_series, ttm_fin
from ky_core.storage import Repository


def _score_from_fins(
    symbol: str,
    now: dict[str, Any] | None,
    prior: dict[str, Any] | None,
    as_of: str | None,
) -> dict[str, Any] | None:
    """Pure function: score from pre-fetched TTM snapshots (no I/O)."""
    if not now:
        return None
    flags: dict[str, int | None] = {}

    # 1. ROA > 0
    roa_now = _safe_div(now.get("net_income_ttm"), now.get("total_assets"))
    flags["roa_positive"] = _bool_int(roa_now is not None and roa_now > 0) if roa_now is not None else None

    # 2. CFO > 0 — unavailable.
    flags["cfo_positive"] = None

    # 3. ΔROA > 0
    roa_prev = _safe_div((prior or {}).get("net_income_ttm"), (prior or {}).get("total_assets"))
    d_roa = (roa_now or 0) - (roa_prev or 0) if (roa_now is not None and roa_prev is not None) else None
    flags["delta_roa"] = _bool_int(d_roa is not None and d_roa > 0) if d_roa is not None else None

    # 4. CFO > NI — unavailable.
    flags["accrual"] = None

    # 5. Δleverage < 0
    dr_now = _safe_div(now.get("total_liabilities"), now.get("total_assets"))
    dr_prev = _safe_div((prior or {}).get("total_liabilities"), (prior or {}).get("total_assets"))
    d_lev = (dr_now or 0) - (dr_prev or 0) if (dr_now is not None and dr_prev is not None) else None
    flags["delta_leverage"] = _bool_int(d_lev is not None and d_lev < 0) if d_lev is not None else None

    # 6. Δliquidity — unavailable.
    flags["delta_liquidity"] = None

    # 7. Δshares — unavailable.
    flags["no_new_shares"] = None

    # 8. Δmargin > 0 (op margin proxy for gross margin)
    om_now = _safe_div(now.get("operating_income_ttm"), now.get("revenue_ttm"))
    om_prev = _safe_div((prior or {}).get("operating_income_ttm"), (prior or {}).get("revenue_ttm"))
    d_om = (om_now or 0) - (om_prev or 0) if (om_now is not None and om_prev is not None) else None
    flags["delta_margin"] = _bool_int(d_om is not None and d_om > 0) if d_om is not None else None

    # 9. Δasset turnover > 0
    at_now = _safe_div(now.get("revenue_ttm"), now.get("total_assets"))
    at_prev = _safe_div((prior or {}).get("revenue_ttm"), (prior or {}).get("total_assets"))
    d_at = (at_now or 0) - (at_prev or 0) if (at_now is not None and at_prev is not None) else None
    flags["delta_turnover"] = _bool_int(d_at is not None and d_at > 0) if d_at is not None else None

    score = sum(v for v in flags.values() if isinstance(v, int))
    max_possible = sum(1 for v in flags.values() if v is not None)
    return {
        "symbol": symbol,
        "as_of": as_of,
        "flags": flags,
        "score": score,
        "max_possible": max_possible,
    }


def piotroski_score(
    symbol: str, *, as_of: str | None = None, repo: Repository | None = None
) -> dict[str, Any] | None:
    """Compute F-Score for one symbol (legacy per-symbol entrypoint)."""
    repo = repo or Repository()
    now = ttm_fin(repo, symbol, as_of=as_of)
    prior = ttm_fin(repo, symbol, as_of=_back_one_year(as_of)) if as_of else None
    return _score_from_fins(symbol, now, prior, as_of)


def piotroski_bulk(
    symbols: list[str],
    *,
    as_of: str,
    repo: Repository | None = None,
) -> dict[str, dict[str, Any]]:
    """Score a whole universe in one pass using bulk PIT reads."""
    from ky_core.quant.pit import ttm_fin_pair_bulk  # local import: avoid cycles
    repo = repo or Repository()
    prior_as_of = _back_one_year(as_of) or as_of
    now_map, prior_map = ttm_fin_pair_bulk(
        repo, symbols, as_of=as_of, prior_as_of=prior_as_of
    )
    out: dict[str, dict[str, Any]] = {}
    for sym in symbols:
        row = _score_from_fins(sym, now_map.get(sym), prior_map.get(sym), as_of)
        if row:
            out[sym] = row
    return out


def _safe_div(num: Any, den: Any) -> float | None:
    if num is None or den in (None, 0):
        return None
    try:
        return num / den
    except ZeroDivisionError:
        return None


def _bool_int(b: bool | None) -> int | None:
    if b is None:
        return None
    return 1 if b else 0


def _back_one_year(as_of: str | None) -> str | None:
    if not as_of:
        return None
    y, m, d = as_of.split("-")
    return f"{int(y) - 1}-{m}-{d}"
