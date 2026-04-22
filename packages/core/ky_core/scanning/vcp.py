"""Simplified VCP (Volatility Contraction Pattern) detector.

Full VCP detection requires wave-by-wave pivot tracking; for the
EOD Chartist dashboard we use a robust approximation:

  1. Compute rolling 20-day true-range volatility (pct).
  2. Count how many successive 20-day windows over the last 80 days
     show a decreasing volatility (contraction step).
  3. Verify the last 20-day avg volume is < 60% of the 60-day avg
     (volume dry-up).
  4. Report "stage" 1..4 based on contraction count & proximity to 52w
     high.

This buys us a deterministic ``VCPStatus`` — coarse, but close enough
for the scanning count columns on the dashboard.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ky_core.scanning.loader import Panel


@dataclass(frozen=True)
class VCPStatus:
    symbol: str
    stage: int                 # 0 none, 1..3 progressive, 4 breakout-ready
    contractions: int
    last_vol_ratio: float      # latest 20d vol / prev 20d vol
    volume_dry_up: bool
    pct_of_52w_high: float     # close / high52w
    score: float               # 0..1 composite
    label: str                 # 'VCP' | 'Base' | 'B.out' | '—'


def detect_vcp(
    symbol: str,
    *,
    panel: Panel,
) -> VCPStatus:
    rows = panel.series.get(symbol) or []
    if len(rows) < 80:
        return _empty(symbol)

    closes = [r["close"] for r in rows]
    highs = [r["high"] or r["close"] for r in rows]
    lows = [r["low"] or r["close"] for r in rows]
    volumes = [r.get("volume") or 0 for r in rows]

    # Volatility proxy: 20-day mean of (high-low)/close
    def vol20(end: int) -> float:
        s = 0.0
        n = 0
        for i in range(max(0, end - 20), end):
            c = closes[i]
            if c <= 0:
                continue
            s += (highs[i] - lows[i]) / c
            n += 1
        return s / n if n else 0.0

    # Look over last 80 days in 4 successive 20-day buckets
    tail = len(closes)
    windows = [vol20(tail - 60), vol20(tail - 40), vol20(tail - 20), vol20(tail)]
    contractions = 0
    for i in range(1, len(windows)):
        if windows[i] < windows[i - 1] * 0.95:
            contractions += 1

    last_ratio = windows[-1] / windows[-2] if windows[-2] > 0 else 1.0

    # Volume dry-up: last 20 avg vs 60d avg
    avg20 = _mean(volumes[-20:])
    avg60 = _mean(volumes[-60:])
    volume_dry_up = avg60 > 0 and avg20 < avg60 * 0.75

    # Position vs 52w high
    hi52 = max(highs[-252:]) if highs[-252:] else max(highs)
    pct_hi = closes[-1] / hi52 if hi52 > 0 else 0.0

    # Stage logic (coarse)
    stage = 0
    if contractions >= 1 and pct_hi >= 0.80:
        stage = 1
    if contractions >= 2 and pct_hi >= 0.90:
        stage = 2
    if contractions >= 2 and pct_hi >= 0.95 and volume_dry_up:
        stage = 3
    if contractions >= 1 and pct_hi >= 1.0 * 0.999:
        stage = 4

    score = min(1.0, 0.25 * contractions + 0.25 * pct_hi + (0.25 if volume_dry_up else 0.0))
    label = _label_for(stage, pct_hi)
    return VCPStatus(
        symbol=symbol,
        stage=stage,
        contractions=contractions,
        last_vol_ratio=last_ratio,
        volume_dry_up=volume_dry_up,
        pct_of_52w_high=pct_hi,
        score=score,
        label=label,
    )


def _label_for(stage: int, pct_hi: float) -> str:
    if stage >= 4:
        return "B.out"
    if stage >= 2:
        return "VCP"
    if pct_hi >= 0.85:
        return "Base"
    return "—"


def _empty(symbol: str) -> VCPStatus:
    return VCPStatus(symbol, 0, 0, 1.0, False, 0.0, 0.0, "—")


def _mean(xs: list[Any]) -> float:
    if not xs:
        return 0.0
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0
