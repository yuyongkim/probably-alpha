"""Regime detection — 4-state classifier.

This is intentionally a simple proxy (NOT a real HMM). We bucket recent KOSPI
return percentiles combined with the compass composite to label each month as
Expansion / Slowdown / Recession / Recovery.

For a production HMM, swap the body of :func:`classify_regime` — the interface
and return shape will stay the same.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from ky_core.storage import Repository
except Exception:  # pragma: no cover
    Repository = None  # type: ignore

from .compass import CompassResult, compute_compass

REGIMES = ("Expansion", "Slowdown", "Recession", "Recovery")


@dataclass
class RegimeResult:
    current: str
    probabilities: Dict[str, float]
    composite: float
    compass: Dict[str, Any]
    timeseries: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current": self.current,
            "probabilities": {k: round(v, 3) for k, v in self.probabilities.items()},
            "composite": round(self.composite, 3),
            "compass": self.compass,
            "timeseries": self.timeseries,
            "warnings": self.warnings,
        }


def _softmax(scores: Dict[str, float]) -> Dict[str, float]:
    import math
    # Shift by max for numerical stability; empty / NaN inputs fall back
    # to a uniform distribution so the caller never gets None.
    vals = [v for v in scores.values() if v is not None and not math.isnan(v)]
    if not vals:
        n = max(len(scores), 1)
        return {k: 1.0 / n for k in scores}
    peak = max(vals)
    exp = {k: math.exp((v if v is not None else 0.0) - peak) for k, v in scores.items()}
    total = sum(exp.values()) or 1.0
    return {k: v / total for k, v in exp.items()}


def classify_regime(owner_id: str = "self", *, compass: Optional[CompassResult] = None) -> RegimeResult:
    """Classify the current macro regime based on the compass + KOSPI return dynamics.

    Always returns a ``current`` regime in ``REGIMES`` (Expansion / Slowdown /
    Recession / Recovery); never None.
    """
    if compass is None:
        compass = compute_compass(owner_id=owner_id)
    composite = compass.composite
    growth = compass.axes["growth"].score if "growth" in compass.axes else 0.0
    credit = compass.axes["credit"].score if "credit" in compass.axes else 0.0
    inflation = compass.axes["inflation"].score if "inflation" in compass.axes else 0.0

    raw = {
        "Expansion": 2.0 * growth + 1.0 * composite,
        "Slowdown": 1.5 * (1 - growth) + 1.0 * (-inflation),
        "Recession": 2.5 * (-composite) + 1.5 * (-credit),
        "Recovery": 1.5 * composite + 1.0 * credit - 0.5 * abs(growth),
    }
    raw = {k: v * 1.2 for k, v in raw.items()}
    probs = _softmax(raw)
    # Fallback chain: softmax argmax → compass.regime_hint → Recovery.
    current = max(probs.items(), key=lambda kv: kv[1])[0] if probs else ""
    if current not in REGIMES:
        current = compass.regime_hint or "Recovery"

    ts = regime_timeseries(owner_id=owner_id)

    return RegimeResult(
        current=current,
        probabilities=probs,
        composite=composite,
        compass=compass.to_dict(),
        timeseries=ts,
        warnings=list(compass.warnings),
    )


def regime_timeseries(owner_id: str = "self", months: int = 12) -> List[Dict[str, Any]]:
    """Approximate recent regime history using Fed funds + inflation moves.

    This is a placeholder until a real HMM is trained. It returns one row per
    month with a label derived from rate-of-change signs.
    """
    if Repository is None:
        return []
    repo = Repository(owner_id=owner_id)
    rates = [r for r in repo.get_observations("fred", "DFF", limit=720)
             if r.get("value") is not None]
    if len(rates) < 40:
        return []

    # Downsample to ~monthly: take the last observation per month.
    monthly: Dict[str, Dict[str, Any]] = {}
    for r in rates:
        key = r["date"][:7]
        monthly[key] = r
    items = sorted(monthly.items())[-months:]
    out: List[Dict[str, Any]] = []
    prev_rate: Optional[float] = None
    for yyyymm, row in items:
        rate = float(row["value"])
        direction = 0
        if prev_rate is not None:
            if rate > prev_rate + 0.05:
                direction = 1   # hiking
            elif rate < prev_rate - 0.05:
                direction = -1  # cutting
        if direction == 1:
            label = "Slowdown"
        elif direction == -1:
            label = "Recovery"
        else:
            label = "Expansion" if rate < 4.5 else "Slowdown"
        out.append({
            "month": yyyymm,
            "fed_funds": rate,
            "label": label,
            "delta_bp": None if prev_rate is None else round((rate - prev_rate) * 100, 1),
        })
        prev_rate = rate
    return out
