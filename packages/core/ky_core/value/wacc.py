"""CAPM-based WACC with capital structure from ``financials_pit``.

Assumptions (documented for the consumer):
- Risk-free rate: 3.0 % (KR 10Y mid-cycle baseline)
- Market premium: 6.0 % (historical MSCI KR excess return)
- Beta: 1.0 (falls back when we don't have time-series vs index yet)
- Tax: 22 % (KR corporate rate)

Callers can override every input. Keep this file deterministic and small.
"""
from __future__ import annotations

from typing import Any

from ky_core.quant.pit import ttm_fin
from ky_core.storage import Repository

DEFAULT_RF = 0.030
DEFAULT_ERP = 0.060
DEFAULT_BETA = 1.0
DEFAULT_COST_OF_DEBT = 0.045
DEFAULT_TAX = 0.22


def cost_of_equity(
    rf: float = DEFAULT_RF,
    erp: float = DEFAULT_ERP,
    beta: float = DEFAULT_BETA,
) -> float:
    """CAPM: r_f + β · ERP."""
    return rf + beta * erp


def wacc(
    symbol: str,
    *,
    as_of: str | None = None,
    rf: float = DEFAULT_RF,
    erp: float = DEFAULT_ERP,
    beta: float = DEFAULT_BETA,
    rd: float = DEFAULT_COST_OF_DEBT,
    tax: float = DEFAULT_TAX,
    repo: Repository | None = None,
) -> dict[str, Any] | None:
    """Compute WACC for a KR listed symbol.

    Weights come from PIT ``total_equity`` and ``total_liabilities``. When
    balance-sheet data is missing (common for ``company_credit_fin`` rows)
    we fall back to a 50 / 50 split and flag ``fallback=True``.
    """
    repo = repo or Repository()
    fin = ttm_fin(repo, symbol, as_of=as_of)
    equity = fin.get("total_equity") if fin else None
    debt = fin.get("total_liabilities") if fin else None
    re = cost_of_equity(rf, erp, beta)
    fallback = False
    if not equity or not debt or equity <= 0 or debt <= 0:
        we = wd = 0.5
        fallback = True
    else:
        total = equity + debt
        we = equity / total
        wd = debt / total
    w = we * re + wd * rd * (1 - tax)
    return {
        "symbol": symbol,
        "as_of": as_of,
        "rf": rf,
        "erp": erp,
        "beta": beta,
        "cost_of_equity": re,
        "cost_of_debt_after_tax": rd * (1 - tax),
        "w_equity": we,
        "w_debt": wd,
        "wacc": w,
        "fallback": fallback,
    }
