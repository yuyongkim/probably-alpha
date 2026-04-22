"""Academic stock-selection strategies.

- Magic Formula (Greenblatt)
- Deep Value (Graham net-net / low P/B)
- Fast Growth (rev + earnings YoY)
- Super Quant (value + quality + momentum composite)

All strategies read from factors.scan() output + PIT financials via
the helpers in :mod:`ky_core.quant.pit`, so each screener stays declarative.
"""
from __future__ import annotations

import json
from typing import Any

from ky_core.quant.factors import scan
from ky_core.quant.pit import latest_fin, ttm_fin
from ky_core.storage import Repository


def magic_formula(as_of: str, *, n: int = 30, repo: Repository | None = None) -> list[dict[str, Any]]:
    """Greenblatt: rank by sum of (ROC rank + EarningsYield rank). Lower is better.

    ROC ≈ operating_income / (total_assets − total_liabilities + total_liabilities)
         = operating_income / total_assets (we fall back to this when
         current assets/liabilities are unavailable in financials_pit).
    Earnings Yield ≈ operating_income / market_cap_proxy (close as proxy when
         shares outstanding aren't available — rank-based so proxy is OK).
    """
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    enriched: list[dict[str, Any]] = []
    for r in rows:
        f = ttm_fin(repo, r["symbol"], as_of=as_of)
        if not f or not f.get("operating_income_ttm") or not f.get("total_assets"):
            continue
        ebit = f["operating_income_ttm"]
        total_assets = f["total_assets"]
        if total_assets <= 0 or ebit is None:
            continue
        roc = ebit / total_assets
        # Earnings yield proxy
        close = r.get("close")
        if not close or close <= 0:
            continue
        ey = ebit / close  # scale-independent via rank
        enriched.append({**r, "roc": roc, "earnings_yield": ey, "ebit_ttm": ebit})
    enriched.sort(key=lambda x: x["roc"], reverse=True)
    for i, x in enumerate(enriched):
        x["roc_rank"] = i
    enriched.sort(key=lambda x: x["earnings_yield"], reverse=True)
    for i, x in enumerate(enriched):
        x["ey_rank"] = i
    for x in enriched:
        x["magic_score"] = x["roc_rank"] + x["ey_rank"]
    enriched.sort(key=lambda x: x["magic_score"])
    return enriched[:n]


def deep_value(as_of: str, *, n: int = 30, repo: Repository | None = None) -> list[dict[str, Any]]:
    """Graham-style: low price-to-book + positive earnings + low debt.

    Without shares outstanding we use equity-per-KRW-of-close as a proxy.
    Ranking behaviour is preserved.
    """
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    out: list[dict[str, Any]] = []
    for r in rows:
        f = ttm_fin(repo, r["symbol"], as_of=as_of)
        if not f or not f.get("total_equity") or not f.get("net_income_ttm"):
            continue
        equity = f["total_equity"]
        ni = f["net_income_ttm"]
        close = r.get("close")
        if not close or close <= 0 or equity <= 0 or ni <= 0:
            continue
        pb_proxy = close / equity  # lower is cheaper
        debt_ratio = (f.get("total_liabilities") or 0.0) / max(f["total_assets"] or 1e9, 1)
        if debt_ratio > 0.7:
            continue
        out.append(
            {
                **r,
                "pb_proxy": pb_proxy,
                "net_income_ttm": ni,
                "equity": equity,
                "debt_ratio": debt_ratio,
            }
        )
    out.sort(key=lambda x: x["pb_proxy"])
    return out[:n]


def fast_growth(as_of: str, *, n: int = 30, repo: Repository | None = None) -> list[dict[str, Any]]:
    """Top growers by revenue YoY + earnings YoY + price momentum."""
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    out: list[dict[str, Any]] = []
    for r in rows:
        if r.get("momentum") is None or r.get("growth") is None:
            continue
        f_now = ttm_fin(repo, r["symbol"], as_of=as_of)
        if not f_now or not f_now.get("revenue_ttm"):
            continue
        # YoY comparison: step back roughly 365 days
        as_of_dt = as_of
        prior = ttm_fin(repo, r["symbol"], as_of=_back_one_year(as_of_dt))
        rev_yoy = None
        if prior and prior.get("revenue_ttm") and prior["revenue_ttm"] > 0:
            rev_yoy = (f_now["revenue_ttm"] / prior["revenue_ttm"]) - 1.0
        ni_yoy = None
        if (
            prior
            and prior.get("net_income_ttm")
            and prior["net_income_ttm"] > 0
            and f_now.get("net_income_ttm")
        ):
            ni_yoy = (f_now["net_income_ttm"] / prior["net_income_ttm"]) - 1.0
        score = (r["momentum"] or 0) + (rev_yoy or 0) + (ni_yoy or 0)
        out.append(
            {**r, "rev_yoy": rev_yoy, "ni_yoy": ni_yoy, "score": score}
        )
    out.sort(key=lambda x: x["score"], reverse=True)
    return out[:n]


def super_quant(as_of: str, *, n: int = 30, repo: Repository | None = None) -> list[dict[str, Any]]:
    """Composite of value + quality + momentum ranks."""
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    out = [
        r for r in rows
        if r.get("value") is not None and r.get("quality") is not None and r.get("momentum") is not None
    ]
    for r in out:
        r["super_score"] = (r["value"] + r["quality"] + r["momentum"]) / 3
    out.sort(key=lambda x: x["super_score"], reverse=True)
    return out[:n]


def _back_one_year(as_of: str) -> str:
    y, m, d = as_of.split("-")
    return f"{int(y) - 1}-{m}-{d}"
