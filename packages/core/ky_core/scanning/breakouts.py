"""52-week breakout scanner.

A "breakout" here means: today's close ≥ 252-day closing high
and today's volume ≥ ``vol_x_min`` × 50-day avg volume.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date as _date
from typing import Any

from ky_core.scanning.loader import Panel, load_panel


@dataclass
class BreakoutRow:
    symbol: str
    name: str
    market: str
    sector: str
    close: float
    pct_up: float        # 1-day change pct
    vol_x: float         # today vol / 50d avg
    high52w: float


def scan_breakouts(
    as_of: _date | str | None = None,
    *,
    panel: Panel | None = None,
    vol_x_min: float = 1.5,
    limit: int = 100,
) -> list[BreakoutRow]:
    panel = panel or load_panel(as_of)
    out: list[BreakoutRow] = []
    for sym, rows in panel.series.items():
        if len(rows) < 60:
            continue
        closes = [r["close"] for r in rows]
        highs = [r["high"] or r["close"] for r in rows]
        vols = [r.get("volume") or 0 for r in rows]

        hi52 = max(highs[-252:]) if len(highs) >= 252 else max(highs)
        close = closes[-1]
        if close < hi52 * 0.999:  # tiny tolerance
            continue

        avg50 = sum(vols[-50:]) / max(1, min(50, len(vols)))
        vol_x = (vols[-1] / avg50) if avg50 > 0 else 0.0
        if vol_x < vol_x_min:
            continue

        prev = closes[-2] if len(closes) >= 2 else close
        pct_up = (close / prev - 1.0) * 100 if prev > 0 else 0.0

        meta = panel.universe.get(sym, {})
        out.append(
            BreakoutRow(
                symbol=sym,
                name=meta.get("name") or sym,
                market=meta.get("market") or "UNKNOWN",
                sector=meta.get("sector") or "기타",
                close=close,
                pct_up=pct_up,
                vol_x=vol_x,
                high52w=hi52,
            )
        )
    out.sort(key=lambda b: b.vol_x * max(0.5, b.pct_up / 5), reverse=True)
    return out[:limit]


def to_dict(b: BreakoutRow) -> dict[str, Any]:
    return asdict(b)
