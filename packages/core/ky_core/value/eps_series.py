"""EPS time-series reader.

Ported from Company_Credit ``sepa.data.fundamentals``.  The reference
implementation there had four source chains (QuantDB long history + NaverComp
cF3002 + Naver mobile EPS + NI/shares recalc).  ky-platform only keeps the
sources that are live in ``ky.db``:

* **Primary (quarterly & annual):** rows in ``financial_statements_db`` whose
  ``account_name`` contains 주당순이익 (``%주당%순이익%``).  NaverComp publishes
  both plain 주당순이익 and (지배주주지분)주당순이익 — we prefer the plain form
  but fall back to the 지배주주 variant when only the latter exists.  Diluted
  rows (희석주당순이익) are kept as a last resort.
* **Secondary (computed):** ``financials_pit.net_income`` divided by a
  shares-outstanding proxy derived from equity × P/B ≈ 1.5 / latest close (the
  same heuristic ``value.dcf.shares_outstanding_proxy`` already uses).

We intentionally skip the Company_Credit ``meta.db`` shares table and the
QuantDB snapshot — ky-platform does not ship those yet.  When the primary
source is missing the fallback is explicitly flagged via ``source='ni_proxy'``
so the UI can badge degraded rows.

Period convention:

- Annual rows have ``period`` = ``"2024"`` and ``period_type='annual'``.
- Quarterly rows have ``period`` = ``"2024Q4"`` and ``period_type='quarterly'``.
- ``available_date`` is the earliest ISO date (YYYY-MM-DD) the row may be used
  to avoid look-ahead bias (fiscal quarter-end + 45 days, Q4 + 75 days).

Public API:

    get_eps_series(symbol, period='Q', years=5) -> list[EPSPoint]

Returns newest-first.  Each ``EPSPoint`` carries YoY growth when it is
computable (same quarter of the prior year).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any, Iterable, Optional

try:  # absolute import when used in-process
    from ky_core.storage import Repository
except Exception:  # pragma: no cover
    Repository = None  # type: ignore


# Preference order when the same period has multiple 주당순이익 rows.
# Lower number = higher priority.  We prefer the plain (지배주주) basic EPS
# and fall back to diluted when nothing else is available.
_EPS_NAME_PRIORITY = (
    ("*(지배주주지분)주당순이익", 0),
    ("*주당순이익", 1),
    ("*(지배주주지분)희석주당순이익", 2),
    ("*희석주당순이익", 3),
    # Sometimes NaverComp strips the leading asterisk.
    ("(지배주주지분)주당순이익", 0),
    ("주당순이익", 1),
    ("(지배주주지분)희석주당순이익", 2),
    ("희석주당순이익", 3),
)


@dataclass
class EPSPoint:
    """A single EPS observation."""

    period: str          # "2024" or "2024Q4"
    period_type: str     # "annual" | "quarterly"
    available_date: str  # ISO YYYY-MM-DD
    eps: float
    eps_yoy: Optional[float]  # percent, or None if prior-year is missing/zero
    source: str          # "statements" | "ni_proxy"
    is_estimate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _strip_suffix(symbol: str) -> str:
    s = symbol.upper().strip()
    for suffix in (".KS", ".KQ"):
        if s.endswith(suffix):
            return s[: -len(suffix)]
    return s


def _period_available_date(period: str, period_type: str) -> str:
    """Return the ISO date after which a row may be used.

    Mirrors Company_Credit: Q1/Q2/Q3 +45 days, Q4 +75 days, annuals use the
    prior-year March 15 (45-day lag on Dec-31 + buffer).
    """
    raw = (period or "").strip().upper()
    try:
        if period_type == "annual" or (len(raw) == 4 and raw.isdigit()):
            year = int(raw[:4])
            return (date(year, 12, 31) + timedelta(days=75)).isoformat()
        if len(raw) == 6 and raw.endswith(("Q1", "Q2", "Q3", "Q4")):
            year = int(raw[:4])
            quarter = raw[-2:]
            mapping = {
                "Q1": (date(year, 3, 31), 45),
                "Q2": (date(year, 6, 30), 45),
                "Q3": (date(year, 9, 30), 45),
                "Q4": (date(year, 12, 31), 75),
            }
            quarter_end, lag = mapping[quarter]
            return (quarter_end + timedelta(days=lag)).isoformat()
    except (ValueError, KeyError):
        pass
    return ""


def _pick_eps_row(candidates: Iterable[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Collapse multiple account_name variants for one period → single row.

    We keep the highest-priority (lowest number) match per the mapping above.
    Rows with non-matching account_names are rejected up-stream so only 주당순이익
    variants reach this function.
    """
    best: Optional[tuple[int, dict[str, Any]]] = None
    for row in candidates:
        name = (row.get("account_name") or "").strip()
        prio = None
        for needle, rank in _EPS_NAME_PRIORITY:
            if name.replace(" ", "") == needle.replace(" ", ""):
                prio = rank
                break
        if prio is None:
            # unknown variant (e.g. locale), accept as lowest priority
            prio = 99
        if best is None or prio < best[0]:
            best = (prio, row)
    return best[1] if best else None


def _read_statement_eps(
    repo: Repository,
    symbol: str,
    *,
    period_type_filter: str | None,
) -> list[EPSPoint]:
    """Read EPS rows from ``financial_statements_db``.

    Groups by ``(period, period_type)`` and collapses duplicate variants via
    :func:`_pick_eps_row`.  Skips ``is_estimate=True`` rows — consumers can
    layer consensus on top if they want forward EPS.
    """
    sym = _strip_suffix(symbol)
    # Pull a generous window and filter in-memory; get_statements already
    # returns newest-first and does not push account_name filters, so we do
    # the 주당순이익 filter here.
    all_rows = repo.get_statements(sym, period_type=period_type_filter, limit=4000)
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in all_rows:
        if row.get("is_estimate"):
            continue
        name = (row.get("account_name") or "").strip()
        # fast string filter — 주당순이익 always appears somewhere in the name
        if "주당" not in name or "순이익" not in name:
            continue
        key = (row["period"], row["period_type"])
        buckets.setdefault(key, []).append(row)

    picks: list[EPSPoint] = []
    for (period, ptype), rows in buckets.items():
        chosen = _pick_eps_row(rows)
        if chosen is None or chosen.get("value") is None:
            continue
        try:
            eps = float(chosen["value"])
        except (TypeError, ValueError):
            continue
        picks.append(
            EPSPoint(
                period=period,
                period_type=ptype,
                available_date=_period_available_date(period, ptype),
                eps=eps,
                eps_yoy=None,  # filled in later
                source="statements",
                is_estimate=False,
            )
        )
    return picks


def _shares_outstanding_proxy(
    repo: Repository,
    symbol: str,
    equity: Optional[float],
    as_of: Optional[str],
) -> Optional[float]:
    """Borrowed from ``value.dcf.shares_outstanding_proxy``.

    We do not import it to keep the module self-contained (circular
    imports become a nuisance when dcf evolves).
    """
    if not equity:
        return None
    try:
        from ky_core.quant.pit import latest_price
    except Exception:  # pragma: no cover
        return None
    px = latest_price(repo, symbol, as_of=as_of) or {}
    close = px.get("close")
    if not close:
        return None
    # equity comes from financials_pit in KRW (억 or raw — we don't know here
    # without reading meta, so we trust the pit layer's normalisation).
    # Price-to-book ≈ 1.5 is the same assumption dcf.py makes.
    return float(equity) * 1.5 / float(close)


def _read_ni_proxy_eps(
    repo: Repository,
    symbol: str,
    *,
    as_of: Optional[str],
) -> list[EPSPoint]:
    """Fallback — compute EPS from net_income / shares_outstanding_proxy.

    Reads ``financials_pit`` rows (annual only — quarterly net_income is
    often missing) and divides by the equity-based shares proxy.  This only
    fires when the primary statement source returns nothing.
    """
    sym = _strip_suffix(symbol)
    try:
        with repo.session() as sess:  # type: ignore[attr-defined]
            from ky_core.storage.schema import FinancialPIT  # local import
            from sqlalchemy import select

            stmt = select(FinancialPIT).where(
                FinancialPIT.symbol == sym,
                FinancialPIT.owner_id == repo.owner_id,
            ).order_by(FinancialPIT.period_end.desc())
            rows = sess.execute(stmt).scalars().all()
            fin_rows = [
                {
                    "period_end": r.period_end,
                    "period_type": r.period_type,
                    "net_income": r.net_income,
                    "total_equity": r.total_equity,
                }
                for r in rows
            ]
    except Exception:
        return []

    if not fin_rows:
        return []

    # Use the most-recent equity as a stable shares proxy.
    latest_eq = next((r["total_equity"] for r in fin_rows if r["total_equity"]), None)
    shares = _shares_outstanding_proxy(repo, sym, latest_eq, as_of)
    if not shares or shares <= 0:
        return []

    out: list[EPSPoint] = []
    for row in fin_rows:
        ni = row.get("net_income")
        if ni is None:
            continue
        period_end = row.get("period_end") or ""
        period_type = row.get("period_type") or "FY"
        if period_type == "FY" and len(period_end) >= 4:
            period = period_end[:4]
            ptype = "annual"
        elif period_type in ("Q1", "Q2", "Q3", "Q4") and len(period_end) >= 4:
            period = f"{period_end[:4]}{period_type}"
            ptype = "quarterly"
        else:
            continue
        try:
            eps = float(ni) / float(shares)
        except (TypeError, ValueError, ZeroDivisionError):
            continue
        out.append(
            EPSPoint(
                period=period,
                period_type=ptype,
                available_date=_period_available_date(period, ptype),
                eps=round(eps, 2),
                eps_yoy=None,
                source="ni_proxy",
                is_estimate=False,
            )
        )
    return out


def _prev_period(period: str, period_type: str) -> Optional[str]:
    try:
        if period_type == "annual" and len(period) == 4 and period.isdigit():
            return str(int(period) - 1)
        if period_type == "quarterly" and len(period) == 6 and period[4] == "Q":
            year = int(period[:4])
            q = period[5]
            return f"{year - 1}Q{q}"
    except ValueError:
        return None
    return None


def _compute_yoy(points: list[EPSPoint]) -> list[EPSPoint]:
    by_key: dict[str, EPSPoint] = {p.period: p for p in points}
    for p in points:
        prev_key = _prev_period(p.period, p.period_type)
        prev = by_key.get(prev_key) if prev_key else None
        if prev and abs(prev.eps) > 0.001:
            p.eps_yoy = round(((p.eps - prev.eps) / abs(prev.eps)) * 100.0, 2)
    return points


def get_eps_series(
    symbol: str,
    *,
    period: str = "Q",
    years: int = 5,
    as_of: Optional[str] = None,
    repo: Optional[Repository] = None,
) -> list[EPSPoint]:
    """Return EPS history for ``symbol``.

    Args:
        symbol: KRX ticker (``005930`` or ``005930.KS``).
        period: ``"Q"`` for quarterly (default), ``"A"`` / ``"FY"`` for annual,
            ``"ALL"`` to return both.
        years: lookback window in years.  Quarterly returns ~years × 4 rows;
            annual returns up to ``years`` rows.
        as_of: ISO date cutoff for look-ahead guard.  Points whose
            ``available_date`` > ``as_of`` are dropped.
        repo: override the default ``Repository`` (useful for tests).

    Returns newest-first.  Empty list when no sources have data.
    """
    if Repository is None:  # pragma: no cover
        return []
    if repo is None:
        repo = Repository()

    period_up = (period or "Q").strip().upper()
    if period_up in ("A", "FY", "ANNUAL"):
        filter_type = "annual"
    elif period_up in ("Q", "QUARTERLY"):
        filter_type = "quarterly"
    elif period_up == "ALL":
        filter_type = None
    else:
        filter_type = "quarterly"

    # Primary source first — NaverComp statements.
    points = _read_statement_eps(repo, symbol, period_type_filter=filter_type)

    # Fallback only if primary returned nothing.
    if not points:
        fallback = _read_ni_proxy_eps(repo, symbol, as_of=as_of)
        if filter_type:
            fallback = [p for p in fallback if p.period_type == filter_type]
        points = fallback

    if not points:
        return []

    # Look-ahead guard.
    if as_of:
        points = [
            p for p in points
            if not p.available_date or p.available_date <= as_of
        ]

    # Newest-first sort.  Use (year, quarter) tuple to sort correctly.
    def _sort_key(p: EPSPoint) -> tuple[int, int]:
        year = int(p.period[:4]) if p.period[:4].isdigit() else 0
        q = 4 if p.period_type == "annual" else (
            int(p.period[5]) if len(p.period) == 6 and p.period[5].isdigit() else 0
        )
        return (year, q)

    points.sort(key=_sort_key)
    points = _compute_yoy(points)
    points.reverse()  # newest-first

    # Trim to requested window.
    if filter_type == "annual" or period_up in ("A", "FY", "ANNUAL"):
        limit = max(1, years)
    elif period_up == "ALL":
        limit = max(1, years * 5)  # allow both annuals + quarters
    else:
        limit = max(1, years * 4)

    return points[:limit]


def eps_growth_snapshot(
    symbol: str,
    *,
    as_of: Optional[str] = None,
    repo: Optional[Repository] = None,
) -> dict[str, Any]:
    """Minervini-style EPS growth classification.

    Returns ``{'status': 'explosive'|'strong'|'improving'|'weak'|'missing',
    'latest_yoy': float, 'acceleration': float, 'growth_hint': float}``.
    Parity with ``Company_Credit.sepa.data.fundamentals.eps_growth_snapshot``.
    """
    series = get_eps_series(symbol, period="Q", years=3, as_of=as_of, repo=repo)
    if not series:
        return {
            "status": "missing",
            "latest_yoy": 0.0,
            "acceleration": 0.0,
            "growth_hint": 0.5,
        }

    yoy_values = [p.eps_yoy for p in series if p.eps_yoy is not None]
    if not yoy_values:
        return {
            "status": "missing",
            "latest_yoy": 0.0,
            "acceleration": 0.0,
            "growth_hint": 0.5,
        }
    # series is newest-first → yoy_values[0] is latest.
    latest_yoy = float(yoy_values[0])
    acceleration = (
        latest_yoy - float(yoy_values[1]) if len(yoy_values) >= 2 else 0.0
    )
    if latest_yoy >= 25 and acceleration >= 0:
        status, growth_hint = "explosive", 2.0
    elif latest_yoy >= 15:
        status, growth_hint = "strong", 1.5
    elif latest_yoy > 0:
        status, growth_hint = "improving", 1.0
    else:
        status, growth_hint = "weak", 0.5
    return {
        "status": status,
        "latest_yoy": round(latest_yoy, 2),
        "acceleration": round(acceleration, 2),
        "growth_hint": growth_hint,
    }


__all__ = ["EPSPoint", "get_eps_series", "eps_growth_snapshot"]
