"""Macro compass — 4-axis scoring from stored observations.

Axes:

- **growth**     : US GDP YoY + DEXUSEU movement (proxies for global growth)
- **inflation**  : CPI / Core CPI YoY change (higher = more hawkish pressure)
- **liquidity**  : M2 growth YoY + Fed Funds rate direction (looser = higher)
- **credit**     : Corporate bond spread (BAA10Y / AAA10Y). Wider = worse.

Each axis is normalised to ``[-1.0, +1.0]`` where ``+1`` is the most supportive
for risk assets and ``-1`` is the most restrictive. We use ``tanh`` compression
on the raw change so a single hot datapoint (e.g. GDP +17%) doesn't saturate
the axis — a 10% change now maps to ~0.76 instead of clipping at 1.00.

The implementation is intentionally conservative: if an indicator is missing we
fall back to a neutral 0.0 for that axis — never inventing data.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:  # absolute import when used in-process
    from ky_core.storage import Repository
except Exception:  # pragma: no cover
    Repository = None  # type: ignore

AXIS_IDS = ("growth", "inflation", "liquidity", "credit")

# Preferred FRED series per axis. We try these in order; first one with >=2
# non-null observations wins. This keeps the compass resilient when only a
# subset of series has been collected.
_FRED_CANDIDATES: Dict[str, List[str]] = {
    "growth": ["GDPC1", "GDP", "INDPRO", "PAYEMS"],
    "inflation": ["CPILFESL", "CPIAUCSL", "PCEPILFE"],
    "liquidity": ["M2SL", "WM2NS", "DFF"],       # DFF inverted (higher rate = tighter)
    "credit": ["BAA10Y", "BAA10YM", "AAA10Y"],   # wider = worse
}


# --------------------------------------------------------------------------- #
# Dataclasses                                                                 #
# --------------------------------------------------------------------------- #


@dataclass
class AxisDetail:
    axis: str
    score: float          # [-1, +1]; +1 = supportive
    series_id: Optional[str]
    latest_value: Optional[float]
    prior_value: Optional[float]
    change_pct: Optional[float]   # % change, latest vs prior (if numeric)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "axis": self.axis,
            "score": round(self.score, 3),
            "series_id": self.series_id,
            "latest_value": self.latest_value,
            "prior_value": self.prior_value,
            "change_pct": self.change_pct,
            "note": self.note,
        }


@dataclass
class CompassResult:
    axes: Dict[str, AxisDetail]
    composite: float          # avg of axes, [-1, +1]
    regime_hint: str          # Expansion | Slowdown | Recession | Recovery
    generated_at: str = ""
    stale: bool = False
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        # Guarantee a non-null string so the UI never sees `regime: null`.
        regime = self.regime_hint or "Recovery"
        return {
            "axes": {k: v.to_dict() for k, v in self.axes.items()},
            "composite": round(self.composite, 3),
            "regime_hint": regime,
            # Alias exposed because several consumers (rotation page,
            # web/types/macro.ts::CompassResponse) read a flat `regime` field.
            "regime": regime,
            "generated_at": self.generated_at,
            "stale": self.stale,
            "warnings": self.warnings,
        }


# --------------------------------------------------------------------------- #
# Scoring                                                                     #
# --------------------------------------------------------------------------- #


def _clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _pct_change(latest: float, prior: float) -> Optional[float]:
    if prior == 0 or prior is None:
        return None
    try:
        return (latest - prior) / abs(prior)
    except Exception:
        return None


def _score_growth(change: float) -> float:
    # tanh compression so extreme prints (e.g. GDP +17% in a short sample)
    # settle around ~0.70 instead of clipping to 1.00. Scale 0.20 means a
    # +20% change maps to tanh(1.0) ≈ 0.76 — and +17% to ~0.70. The old
    # linear scheme (change/0.04) saturated at 4%.
    return _clip(math.tanh(change / 0.20))


def _score_inflation(change: float) -> float:
    # Higher CPI YoY = more restrictive = negative for risk.
    # tanh(change/0.02) maps 2% to -0.76, 4% to ~-0.96, 0% to 0. Flip sign
    # because inflation is bad for risk.
    return _clip(-math.tanh(change / 0.02))


def _score_liquidity(change: float, series_id: str) -> float:
    if series_id == "DFF":
        # higher Fed funds = tighter liquidity. tanh keeps extremes bounded.
        return _clip(-math.tanh(change / 0.1))
    # M2 growth: ~2% neutral, 10% hot, 0% crunch. Shift then compress.
    return _clip(math.tanh((change - 0.02) / 0.05))


def _score_credit(latest: float) -> float:
    # BAA-AAA spread in pct: 1% normal, >3% distress.
    if latest is None:
        return 0.0
    # 0.5% ⇒ +1, 1.5% ⇒ 0, 3.0%+ ⇒ -1
    return _clip(1.0 - (latest - 0.5) / 1.25)


def _classify_composite(composite: float) -> str:
    """Deterministic 4-state map — never returns None."""
    if composite is None or math.isnan(composite):
        return "Recovery"
    if composite >= 0.25:
        return "Expansion"
    if composite >= 0.0:
        return "Recovery"
    if composite >= -0.25:
        return "Slowdown"
    return "Recession"


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def _pick_series(repo: "Repository", candidates: List[str]) -> tuple[Optional[str], List[Dict[str, Any]]]:
    """Return (series_id, rows) for the first candidate with ≥2 obs."""
    for sid in candidates:
        rows = repo.get_observations("fred", sid, limit=48)
        # Some legacy series land under ecos; FRED is the primary.
        if len([r for r in rows if r.get("value") is not None]) >= 2:
            return sid, rows
    return None, []


def compute_compass(owner_id: str = "self") -> CompassResult:
    """Compute a snapshot of the 4-axis macro compass from stored observations."""
    if Repository is None:
        return CompassResult(
            axes={a: AxisDetail(a, 0.0, None, None, None, None, "storage unavailable")
                  for a in AXIS_IDS},
            composite=0.0,
            regime_hint="Recovery",  # neutral composite -> Recovery band
            stale=True,
            warnings=["ky_core.storage not importable"],
        )
    repo = Repository(owner_id=owner_id)
    axes: Dict[str, AxisDetail] = {}
    warnings: List[str] = []

    for axis in AXIS_IDS:
        sid, rows = _pick_series(repo, _FRED_CANDIDATES[axis])
        non_null = [r for r in rows if r.get("value") is not None]
        if sid is None or len(non_null) < 2:
            axes[axis] = AxisDetail(axis, 0.0, None, None, None, None,
                                    "insufficient data — neutral fallback")
            warnings.append(f"{axis}: insufficient data")
            continue
        latest = float(non_null[-1]["value"])
        # YoY-ish: look back ~12 months (≤12 entries) but gracefully fall back.
        prior_idx = max(0, len(non_null) - 13)
        prior = float(non_null[prior_idx]["value"])
        change = _pct_change(latest, prior)
        if change is None:
            score = 0.0
            note = "no usable change"
        else:
            if axis == "growth":
                score = _score_growth(change)
            elif axis == "inflation":
                score = _score_inflation(change)
            elif axis == "liquidity":
                score = _score_liquidity(change, sid)
            elif axis == "credit":
                # credit uses level, not change
                score = _score_credit(latest)
            else:
                score = 0.0
            # ASCII-only note so downstream cp949/cp1252 renderers don't
            # mojibake the output. Was previously prefixed with 'Δ'.
            note = f"delta {change * 100:+.2f}% over ~{len(non_null) - prior_idx} obs"
        axes[axis] = AxisDetail(
            axis=axis,
            score=score,
            series_id=sid,
            latest_value=latest,
            prior_value=prior,
            change_pct=change,
            note=note,
        )

    composite = sum(a.score for a in axes.values()) / len(axes)
    from datetime import datetime

    # Regime hint is a light classification; the full enum is in regime.py.
    # Always returns one of the four labels — never None.
    hint = _classify_composite(composite)

    return CompassResult(
        axes=axes,
        composite=composite,
        regime_hint=hint,
        generated_at=datetime.utcnow().isoformat(),
        stale=bool(warnings),
        warnings=warnings,
    )


# --------------------------------------------------------------------------- #
# Sector playbook                                                             #
# --------------------------------------------------------------------------- #

_PLAYBOOK: Dict[str, List[Dict[str, Any]]] = {
    "Expansion": [
        {"sector": "반도체", "rationale": "경기 확장 + 유동성 지지 조합에서 성장주 반도체가 알파"},
        {"sector": "AI/SW", "rationale": "자본지출 확대 국면 수혜"},
        {"sector": "산업재/기계", "rationale": "투자 사이클 확장"},
    ],
    "Recovery": [
        {"sector": "2차전지", "rationale": "신용스프레드 축소 + 성장 반등 초기"},
        {"sector": "조선", "rationale": "수주 모멘텀 회복"},
        {"sector": "화학", "rationale": "재고 사이클 바닥 탈출"},
    ],
    "Slowdown": [
        {"sector": "필수소비재", "rationale": "수익 안정성 + 배당"},
        {"sector": "통신", "rationale": "방어적 성격"},
        {"sector": "제약", "rationale": "경기 민감도 낮음"},
    ],
    "Recession": [
        {"sector": "유틸리티", "rationale": "현금흐름 방어"},
        {"sector": "금", "rationale": "헤지"},
        {"sector": "미국 단기국채", "rationale": "신용 리스크 회피"},
    ],
    "Unknown": [],
}


def sector_playbook(regime: str) -> List[Dict[str, Any]]:
    return list(_PLAYBOOK.get(regime, _PLAYBOOK.get("Unknown", [])))
