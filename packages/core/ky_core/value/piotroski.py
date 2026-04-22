"""Piotroski F-Score (9 binary signals)."""
from __future__ import annotations

from typing import Any

from ky_core.quant.pit import fin_series, ttm_fin
from ky_core.storage import Repository


def piotroski_score(
    symbol: str, *, as_of: str | None = None, repo: Repository | None = None
) -> dict[str, Any] | None:
    """Compute F-Score. Returns dict with 9 flags and the total.

    Where a specific signal can't be evaluated (missing data) we mark it
    ``None`` and do not add to the score — the maximum drops, which is
    preferable to flattering the score.
    """
    repo = repo or Repository()
    now = ttm_fin(repo, symbol, as_of=as_of)
    prior = ttm_fin(repo, symbol, as_of=_back_one_year(as_of)) if as_of else None
    if not now:
        return None
    flags: dict[str, int | None] = {}
    score = 0
    max_possible = 0

    # 1. ROA > 0
    roa_now = _safe_div(now.get("net_income_ttm"), now.get("total_assets"))
    flags["roa_positive"] = _add(roa_now and roa_now > 0, score_ref=[score := score, max_possible := max_possible])
    if flags["roa_positive"] is not None:
        max_possible += 1
        score += flags["roa_positive"]

    # 2. CFO > 0 — CFO unavailable; proxy via net_income + 20 % add-back? Skip (None).
    flags["cfo_positive"] = None

    # 3. ΔROA > 0
    roa_prev = _safe_div((prior or {}).get("net_income_ttm"), (prior or {}).get("total_assets"))
    d_roa = (roa_now or 0) - (roa_prev or 0) if (roa_now is not None and roa_prev is not None) else None
    flags["delta_roa"] = _bool_int(d_roa is not None and d_roa > 0) if d_roa is not None else None
    _accum(flags["delta_roa"], locals())

    # 4. CFO > NI (accrual quality) — CFO missing, skip
    flags["accrual"] = None

    # 5. Δleverage < 0 (lower debt ratio)
    dr_now = _safe_div(now.get("total_liabilities"), now.get("total_assets"))
    dr_prev = _safe_div((prior or {}).get("total_liabilities"), (prior or {}).get("total_assets"))
    d_lev = (dr_now or 0) - (dr_prev or 0) if (dr_now is not None and dr_prev is not None) else None
    flags["delta_leverage"] = _bool_int(d_lev is not None and d_lev < 0) if d_lev is not None else None
    _accum(flags["delta_leverage"], locals())

    # 6. Δliquidity (current ratio) > 0 — not available; skip.
    flags["delta_liquidity"] = None

    # 7. Δshares outstanding ≤ 0 — not available; skip.
    flags["no_new_shares"] = None

    # 8. Δgross margin > 0 — we approximate via op margin change.
    om_now = _safe_div(now.get("operating_income_ttm"), now.get("revenue_ttm"))
    om_prev = _safe_div((prior or {}).get("operating_income_ttm"), (prior or {}).get("revenue_ttm"))
    d_om = (om_now or 0) - (om_prev or 0) if (om_now is not None and om_prev is not None) else None
    flags["delta_margin"] = _bool_int(d_om is not None and d_om > 0) if d_om is not None else None
    _accum(flags["delta_margin"], locals())

    # 9. Δasset turnover > 0
    at_now = _safe_div(now.get("revenue_ttm"), now.get("total_assets"))
    at_prev = _safe_div((prior or {}).get("revenue_ttm"), (prior or {}).get("total_assets"))
    d_at = (at_now or 0) - (at_prev or 0) if (at_now is not None and at_prev is not None) else None
    flags["delta_turnover"] = _bool_int(d_at is not None and d_at > 0) if d_at is not None else None
    _accum(flags["delta_turnover"], locals())

    # Recompute totals
    score = sum(v for v in flags.values() if isinstance(v, int))
    max_possible = sum(1 for v in flags.values() if v is not None)
    return {
        "symbol": symbol,
        "as_of": as_of,
        "flags": flags,
        "score": score,
        "max_possible": max_possible,
    }


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


def _add(flag: bool | None, *, score_ref: list[int]) -> int | None:  # helper for chaining
    return _bool_int(flag)


def _accum(_flag: int | None, _scope: dict[str, Any]) -> None:
    """Placeholder — we recompute totals at the end for clarity."""
    return None


def _back_one_year(as_of: str | None) -> str | None:
    if not as_of:
        return None
    y, m, d = as_of.split("-")
    return f"{int(y) - 1}-{m}-{d}"
