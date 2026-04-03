"""Sector Strength Score per LEADER_SCORING_SPEC.md section 1.

SectorScore = RS_20*0.30 + RS_60*0.25 + Breadth_50MA*0.15
            + NearHighRatio*0.15 + (TurnoverTrend/3)*0.15

Exclusions:
- Sectors with < 5 tradeable stocks
- Sectors with total turnover < 10B KRW (placeholder; depends on data availability)
"""
from __future__ import annotations

from sepa.scoring.factors import (
    breadth_above_ma,
    near_high_ratio,
    rs_relative,
    to_percentile,
    turnover_trend,
)


def score_sectors(
    sector_data: dict[str, list[dict]],
    benchmark_closes: list[float],
    *,
    min_stocks: int = 5,
) -> list[dict]:
    """Score all sectors and return sorted list (highest first).

    Parameters
    ----------
    sector_data : dict
        Mapping of sector_name -> list of stock dicts.
        Each stock dict must have ``"closes"`` (list[float]) and optionally
        ``"volumes"`` (list[float]).
    benchmark_closes : list[float]
        Benchmark (e.g. KOSPI) close prices.
    min_stocks : int
        Minimum stocks required in a sector to be scored.
    """
    # Step 1: Compute raw RS for each sector
    sector_rs20: dict[str, float] = {}
    sector_rs60: dict[str, float] = {}
    sector_breadth: dict[str, float] = {}
    sector_near_high: dict[str, float] = {}
    sector_turnover: dict[str, float] = {}
    sector_stock_count: dict[str, int] = {}

    for sector, stocks in sector_data.items():
        if len(stocks) < min_stocks:
            continue

        closes_list = [s["closes"] for s in stocks if s.get("closes")]
        if len(closes_list) < min_stocks:
            continue

        # Sector return = average of stock returns
        sector_closes_avg = _avg_sector_closes(closes_list)

        sector_rs20[sector] = rs_relative(sector_closes_avg, benchmark_closes, 20)
        sector_rs60[sector] = rs_relative(sector_closes_avg, benchmark_closes, 60)
        sector_breadth[sector] = breadth_above_ma(closes_list, window=50)
        sector_near_high[sector] = near_high_ratio(closes_list, threshold=0.80)

        # Turnover trend (use volume sums as proxy for turnover)
        all_volumes = [s.get("volumes", []) for s in stocks if s.get("volumes")]
        if all_volumes:
            sector_vol_sums = _sum_sector_volumes(all_volumes)
            sector_turnover[sector] = turnover_trend(sector_vol_sums)
        else:
            sector_turnover[sector] = 1.0

        sector_stock_count[sector] = len(closes_list)

    if not sector_rs20:
        return []

    # Step 2: Convert RS to percentiles
    rs20_pct = to_percentile(sector_rs20)
    rs60_pct = to_percentile(sector_rs60)

    # Step 3: Compute final scores
    results: list[dict] = []
    for sector in sector_rs20:
        turnover_norm = min(1.0, sector_turnover.get(sector, 1.0) / 3.0)
        score = (
            rs20_pct[sector] * 0.30
            + rs60_pct[sector] * 0.25
            + sector_breadth[sector] * 0.15
            + sector_near_high[sector] * 0.15
            + turnover_norm * 0.15
        )
        results.append({
            "sector": sector,
            "sector_score": round(score, 4),
            "rs_20": round(rs20_pct[sector], 4),
            "rs_60": round(rs60_pct[sector], 4),
            "breadth_50ma": round(sector_breadth[sector], 4),
            "near_high_ratio": round(sector_near_high[sector], 4),
            "turnover_trend": round(sector_turnover.get(sector, 1.0), 4),
            "stock_count": sector_stock_count[sector],
        })

    results.sort(key=lambda x: x["sector_score"], reverse=True)
    return results


def _avg_sector_closes(closes_list: list[list[float]]) -> list[float]:
    """Average close prices across stocks, aligned from the end."""
    max_len = max(len(c) for c in closes_list)
    avg: list[float] = []
    for i in range(max_len):
        vals = []
        for c in closes_list:
            offset = len(c) - max_len + i
            if 0 <= offset < len(c):
                vals.append(c[offset])
        avg.append(sum(vals) / len(vals) if vals else 0.0)
    return avg


def _sum_sector_volumes(volumes_list: list[list[float]]) -> list[float]:
    """Sum volumes across stocks, aligned from the end."""
    max_len = max(len(v) for v in volumes_list)
    sums: list[float] = []
    for i in range(max_len):
        total = 0.0
        for v in volumes_list:
            offset = len(v) - max_len + i
            if 0 <= offset < len(v):
                total += v[offset]
        sums.append(total)
    return sums
