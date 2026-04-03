"""Leader Stock Score per LEADER_SCORING_SPEC.md section 2.

LeaderScore = RS_120*0.25 + TrendTemplate*0.20 + Near52WHigh*0.15
            + VolumeExpansion*0.15 + VolatilityContraction*0.15
            + EarningsProxy*0.10

Gates (fail = excluded):
- TrendTemplate < 5/8
- close < MA50
- Market cap < 300B KRW (when available)
- 20-day avg turnover < 5B KRW (when available)
"""
from __future__ import annotations

from statistics import mean

from sepa.scoring.factors import (
    earnings_proxy,
    near_52w_high,
    to_percentile,
    trend_template_ratio,
    volatility_contraction,
    volume_expansion,
)


def score_stocks(
    stocks: list[dict],
    *,
    min_tt_pass: int = 5,
) -> list[dict]:
    """Score stocks and return sorted list (highest first).

    Parameters
    ----------
    stocks : list[dict]
        Each dict must have:
        - ``symbol`` : str
        - ``closes`` : list[float]
        - ``volumes`` : list[float]
        - ``checks`` : dict[str, bool] (TT 8 conditions)
        - ``rs_percentile`` : float (0~100)
        Optional:
        - ``sector`` : str
        - ``name`` : str
        - ``eps_yoy``, ``roe``, ``opm`` : float
    min_tt_pass : int
        Minimum TT conditions to pass the gate.
    """
    # Gate filtering
    gated: list[dict] = []
    for s in stocks:
        closes = s.get("closes", [])
        checks = s.get("checks", {})

        # Gate: TT minimum
        passed = sum(1 for v in checks.values() if v)
        if passed < min_tt_pass:
            continue

        # Gate: close > MA50
        if len(closes) >= 50:
            ma50 = mean(closes[-50:])
            if closes[-1] <= ma50:
                continue

        gated.append(s)

    if not gated:
        return []

    # Compute RS_120 percentile
    rs_raw = {s["symbol"]: s.get("rs_percentile", 50.0) for s in gated}
    rs_pct = to_percentile(rs_raw)

    results: list[dict] = []
    for s in gated:
        sym = s["symbol"]
        closes = s.get("closes", [])
        volumes = s.get("volumes", [])
        checks = s.get("checks", {})

        tt = trend_template_ratio(checks)
        n52 = near_52w_high(closes)
        vol_exp = volume_expansion(volumes)
        vol_cont = volatility_contraction(closes)
        ep = earnings_proxy(
            eps_yoy=s.get("eps_yoy"),
            roe=s.get("roe"),
            opm=s.get("opm"),
        )

        score = (
            rs_pct.get(sym, 0.5) * 0.25
            + tt * 0.20
            + n52 * 0.15
            + vol_exp * 0.15
            + vol_cont * 0.15
            + ep * 0.10
        )

        results.append({
            "symbol": sym,
            "name": s.get("name", ""),
            "sector": s.get("sector", ""),
            "leader_score": round(score, 4),
            "rs_120_pct": round(rs_pct.get(sym, 0.5), 4),
            "trend_template_score": round(tt, 4),
            "near_52w_high": round(n52, 4),
            "volume_expansion": round(vol_exp, 4),
            "volatility_contraction": round(vol_cont, 4),
            "earnings_proxy": round(ep, 4),
            "trend_checks": checks,
            "reason": _build_reason(tt, n52, vol_cont, ep, rs_pct.get(sym, 0.5)),
        })

    results.sort(key=lambda x: x["leader_score"], reverse=True)
    return results


def _build_reason(tt: float, near_high: float, vol_cont: float, ep: float, rs: float) -> str:
    parts: list[str] = []
    if rs >= 0.7:
        parts.append("RS상위")
    if tt >= 0.875:  # 7/8+
        parts.append(f"TT{int(tt*8)}/8")
    elif tt >= 0.625:  # 5/8+
        parts.append(f"TT{int(tt*8)}/8")
    if vol_cont >= 0.5:
        parts.append("VCP수축진행")
    if near_high >= 0.9:
        parts.append("신고가근접")
    if ep >= 0.6:
        parts.append("실적양호")
    return "+".join(parts) if parts else "기본통과"
