"""Factor IC / IR — simple Pearson correlation between a factor's
percentile rank (t) and forward return (t → t+h)."""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import text

from ky_core.quant.factors import scan
from ky_core.storage import Repository


def _period_days(period: str) -> int:
    period = period.lower().strip()
    if period.endswith("m"):
        return int(period[:-1]) * 21
    if period.endswith("w"):
        return int(period[:-1]) * 5
    if period.endswith("d"):
        return int(period[:-1])
    raise ValueError(f"bad period: {period}")


def _forward_return(repo: Repository, symbol: str, start: str, end: str) -> float | None:
    q = text(
        """
        SELECT date, close FROM ohlcv
         WHERE symbol = :s AND owner_id = :oid
           AND date BETWEEN :start AND :end
         ORDER BY date ASC
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"s": symbol, "oid": repo.owner_id, "start": start, "end": end}).fetchall()
    if len(rows) < 2:
        return None
    first_close = rows[0][1]
    last_close = rows[-1][1]
    if not first_close or first_close <= 0:
        return None
    return (last_close / first_close) - 1.0


def factor_ic(
    factor: str,
    *,
    as_of: str,
    period: str = "6m",
    sample: int = 400,
    repo: Repository | None = None,
) -> dict[str, Any]:
    """Return {factor, period, ic, n, hit_rate} for the stored universe.

    Sample caps the number of symbols so wide scans stay sub-second.
    """
    repo = repo or Repository()
    rows = scan(as_of, repo=repo)
    rows = [r for r in rows if r.get(factor) is not None][:sample]
    horizon = _period_days(period)
    end_dt = (datetime.fromisoformat(as_of) + timedelta(days=int(horizon * 1.5))).date().isoformat()
    xs: list[float] = []
    ys: list[float] = []
    for r in rows:
        fwd = _forward_return(repo, r["symbol"], as_of, end_dt)
        if fwd is None:
            continue
        xs.append(r[factor])
        ys.append(fwd)
    ic = _pearson(xs, ys)
    hit = sum(1 for y in ys if y > 0) / len(ys) if ys else 0.0
    return {
        "factor": factor,
        "period": period,
        "as_of": as_of,
        "n": len(xs),
        "ic": ic,
        "hit_rate": hit,
    }


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)
