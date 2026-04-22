"""Smart-Beta index variants.

Every variant returns the same row shape so the UI can reuse one table:
    {symbol, name, market, sector, weight, score}

Variants: low_vol, quality, momentum, equal_weight, high_div (proxy via
earnings yield until dividend history lands), qmj (Quality Minus Junk),
bab (Betting Against Beta, approximated via 1/vol).
"""
from __future__ import annotations

from typing import Any

from ky_core.quant.factors import scan
from ky_core.storage import Repository


def _pick(rows: list[dict[str, Any]], factor: str, n: int) -> list[dict[str, Any]]:
    filt = [r for r in rows if r.get(factor) is not None]
    filt.sort(key=lambda r: r[factor], reverse=True)
    return filt[:n]


def build(
    variant: str = "equal_weight",
    *,
    as_of: str,
    n: int = 50,
    repo: Repository | None = None,
) -> dict[str, Any]:
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    variant = variant.lower().strip()
    if variant == "low_vol":
        picks = _pick(rows, "low_vol", n)
    elif variant == "quality":
        picks = _pick(rows, "quality", n)
    elif variant == "momentum":
        picks = _pick(rows, "momentum", n)
    elif variant == "equal_weight":
        picks = [r for r in rows if r.get("composite") is not None][:n]
    elif variant == "high_div":
        # Proxy: top earnings-yield == top value rank in our scan
        picks = _pick(rows, "value", n)
    elif variant == "qmj":
        qmj = [
            {**r, "qmj": (r["quality"] + r["low_vol"]) / 2 + (r.get("growth") or 0) * 0.25}
            for r in rows
            if r.get("quality") is not None and r.get("low_vol") is not None
        ]
        qmj.sort(key=lambda x: x["qmj"], reverse=True)
        picks = qmj[:n]
    elif variant == "bab":
        # Betting-against-beta → invest in low-vol, short high-vol. We only
        # report the long leg here.
        picks = _pick(rows, "low_vol", n)
    else:
        raise ValueError(f"unknown variant: {variant}")
    # Weights
    if variant in ("equal_weight",):
        w = 1.0 / max(len(picks), 1)
        for r in picks:
            r["weight"] = w
    else:
        # Score-proportional weights (clipped negative to 0)
        scores = [max(r.get(variant, r.get("composite", 0.0)) or 0.0, 0.0) for r in picks]
        total = sum(scores) or 1.0
        for r, s in zip(picks, scores):
            r["weight"] = s / total
    for r in picks:
        r["score"] = r.get(variant, r.get("composite"))
    return {
        "variant": variant,
        "as_of": as_of,
        "n": len(picks),
        "holdings": [
            {
                "symbol": r["symbol"],
                "name": r.get("name"),
                "market": r.get("market"),
                "sector": r.get("sector"),
                "weight": r.get("weight"),
                "score": r.get("score"),
            }
            for r in picks
        ],
    }


VARIANTS = ("low_vol", "quality", "momentum", "equal_weight", "high_div", "qmj", "bab")
