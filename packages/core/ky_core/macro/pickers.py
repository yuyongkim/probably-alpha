"""Tier-A indicator picker — fallback-chain resolver.

This module exists so Compass / Regime / downstream signal code can ask for
an indicator **by logical name** ("KR_CPI", "US_10Y") without knowing which
provider currently has fresh data. That indirection is the key lever behind
the 200-indicator architecture — when one source drops a feed, the next
tuple in the chain takes over and the rest of the platform keeps working.

The chain-of-tuples structure lives in
``ky_core.storage.presets.MACRO_TIER_A``. Each tuple starts with the
``source_id`` stored in the observations table; the remaining parts locate
the specific series inside that source.

Supported tuple shapes:

- ``("fred",  series_id)``
- ``("ecos",  stat_code, item_code[, freq])``
- ``("kosis", tbl_id[, itm_id, obj_l1, prd_se])``
- ``("exim",)``                        — the EXIM FX snapshot
- ``("eia",   path, series_code)``
- ``("derived", formula_id, *inputs)`` — computed, never hits storage

``pick_indicator`` tries each tuple in order, reading from the Repository
with a cheap ``observations_count > 0`` check before returning the newest
observation. Returning an ``Observation`` (not just a value) lets callers
inspect provenance: ``source_id``, ``series_id``, ``date``, ``meta`` — so
the audit log can say "picked USDKRW from ecos/731Y001 on 2026-04-22".

Deterministic. No network I/O. Safe to call in hot paths.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from ky_core.storage import Repository
except Exception:  # pragma: no cover - storage import-time failure
    Repository = None  # type: ignore[assignment]

from ky_core.storage.presets import MACRO_TIER_A

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Result dataclasses                                                          #
# --------------------------------------------------------------------------- #


@dataclass
class Observation:
    """Lightweight value-object returned by :func:`pick_indicator`.

    We deliberately don't expose the SQLAlchemy ORM object — callers only
    need the fields below and this keeps the boundary clean.
    """

    indicator: str
    source_id: str
    series_id: str
    date: str                 # ISO YYYY-MM-DD
    value: Optional[float]
    unit: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    # How far down the chain we had to go (0 = primary). Useful for ops
    # dashboards — a high fallback_rank means the primary source is dry.
    fallback_rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator": self.indicator,
            "source_id": self.source_id,
            "series_id": self.series_id,
            "date": self.date,
            "value": self.value,
            "unit": self.unit,
            "meta": self.meta,
            "fallback_rank": self.fallback_rank,
        }


@dataclass
class CoverageReport:
    """Output of :func:`coverage_report` — which indicators currently resolve."""

    total: int
    resolved: int
    unresolved: List[str] = field(default_factory=list)
    by_source: Dict[str, int] = field(default_factory=dict)
    by_fallback_rank: Dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "resolved": self.resolved,
            "resolved_pct": round(100.0 * self.resolved / self.total, 1) if self.total else 0.0,
            "unresolved": self.unresolved,
            "by_source": self.by_source,
            "by_fallback_rank": self.by_fallback_rank,
        }


# --------------------------------------------------------------------------- #
# Series-id resolution per source                                             #
# --------------------------------------------------------------------------- #


def _series_id_for_tuple(tup: Tuple[str, ...]) -> Optional[str]:
    """Map a fallback-chain tuple to the ``series_id`` used in observations.

    Returns ``None`` for tuples that don't correspond to a persisted series
    (notably ``("derived", ...)`` — derived indicators never hit storage
    directly; they're computed from already-resolved primitives).
    """
    if not tup:
        return None
    source = tup[0]
    if source == "fred":
        # FRED stores the bare series id as the series_id.
        return tup[1] if len(tup) >= 2 else None
    if source == "ecos":
        # ECOS collector writes series_id="{stat_code}/{item_code}".
        if len(tup) >= 3:
            return f"{tup[1]}/{tup[2]}"
        return None
    if source == "kosis":
        # KOSIS collector writes the C1 bucket into series_id, with the
        # stem ``kosis/{tbl_id}/{itm_id}`` — e.g. ``kosis/DT_1C8015/T1/A00``
        # for the "national leading index, base" bucket. We return the
        # stem so ``_fetch_latest`` can LIKE-match every C1 under it.
        # Tuple shapes accepted:
        #   ("kosis", tbl_id, itm_id, obj_l1[, prd_se])
        #   ("kosis", tbl_id)
        if len(tup) >= 3:
            return f"kosis/{tup[1]}/{tup[2]}"
        if len(tup) >= 2:
            return f"kosis/{tup[1]}"
        return None
    if source == "exim":
        # EXIM collector writes series_id="USDKRW" (and friends).
        return "USDKRW"
    if source == "eia":
        # EIA writes series_id=<series_code>.
        return tup[2] if len(tup) >= 3 else (tup[1] if len(tup) >= 2 else None)
    if source == "derived":
        return None
    return None


def _fetch_latest(
    repo: "Repository", source_id: str, series_id: str
) -> Optional[Observation]:
    """Best-effort newest-row fetch for (source, series).

    KOSIS stores one row per C1 bucket under a shared prefix, so the helper
    supports prefix matching for that source. All other sources go through
    the exact-match fast path.
    """
    from sqlalchemy import text

    if source_id == "kosis":
        # prefix match — observations where series_id starts with series_id/
        # (or equals it, for legacy exact-match rows).
        sql = text(
            """
            SELECT source_id, series_id, date, value, unit, meta
            FROM observations
            WHERE source_id = :src
              AND (series_id = :sid OR series_id LIKE :prefix)
              AND owner_id = :owner
              AND value IS NOT NULL
            ORDER BY date DESC
            LIMIT 1
            """
        )
        params = {
            "src": source_id,
            "sid": series_id,
            "prefix": series_id + "/%",
            "owner": repo.owner_id,
        }
    else:
        sql = text(
            """
            SELECT source_id, series_id, date, value, unit, meta
            FROM observations
            WHERE source_id = :src
              AND series_id = :sid
              AND owner_id = :owner
              AND value IS NOT NULL
            ORDER BY date DESC
            LIMIT 1
            """
        )
        params = {"src": source_id, "sid": series_id, "owner": repo.owner_id}

    with repo.session() as sess:
        row = sess.execute(sql, params).first()
    if not row:
        return None
    # Row order matches the SELECT.
    return Observation(
        indicator="",   # filled by caller
        source_id=row[0],
        series_id=row[1],
        date=row[2],
        value=row[3],
        unit=row[4],
        meta=row[5] if isinstance(row[5], dict) else None,
    )


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def pick_indicator(
    name: str,
    *,
    owner_id: str = "self",
    repo: Optional["Repository"] = None,
    sources: Optional[Iterable[str]] = None,
) -> Optional[Observation]:
    """Return the most recent :class:`Observation` for ``name`` from the
    first resolving source in its fallback chain.

    Parameters
    ----------
    name
        Logical indicator key (must exist in ``MACRO_TIER_A``). Names are
        case-sensitive to keep the contract explicit.
    owner_id
        Tenant scope. Defaults to ``"self"``.
    repo
        Inject a Repository for testing / batch reuse. When ``None`` a
        fresh one is constructed (and closed on the caller's session
        rollback).
    sources
        Optional whitelist — only consider these source ids in the chain
        (order-preserved). Useful for "KR-only" / "US-only" slices.

    Returns
    -------
    Observation | None
        ``None`` when the name isn't registered or no source has data.
    """
    chain = MACRO_TIER_A.get(name)
    if not chain:
        logger.debug("pick_indicator: %s not in MACRO_TIER_A", name)
        return None
    if Repository is None:
        return None
    r = repo or Repository(owner_id=owner_id)
    allow = set(sources) if sources else None

    for rank, tup in enumerate(chain):
        if not tup:
            continue
        source_id = tup[0]
        if allow is not None and source_id not in allow:
            continue
        if source_id == "derived":
            # Derived values are the caller's job — the picker doesn't
            # compute spreads/zscores here to avoid a circular dependency
            # with compass.py.
            continue
        series_id = _series_id_for_tuple(tup)
        if not series_id:
            continue
        obs = _fetch_latest(r, source_id, series_id)
        if obs is None or obs.value is None:
            continue
        obs.indicator = name
        obs.fallback_rank = rank
        return obs

    return None


def pick_many(
    names: Iterable[str],
    *,
    owner_id: str = "self",
    repo: Optional["Repository"] = None,
) -> Dict[str, Optional[Observation]]:
    """Batch variant — resolves a list of names against a single Repository.

    Constructs one repo and reuses it for every pick, which is measurably
    faster than constructing a fresh one per call when the caller needs 30+
    indicators (the compass+regime flow).
    """
    if Repository is None:
        return {n: None for n in names}
    r = repo or Repository(owner_id=owner_id)
    return {name: pick_indicator(name, owner_id=owner_id, repo=r) for name in names}


def coverage_report(
    *,
    owner_id: str = "self",
    repo: Optional["Repository"] = None,
) -> CoverageReport:
    """Walk every indicator in MACRO_TIER_A and report which ones resolve.

    Call this from the ops dashboard to see how many Tier-A indicators are
    currently hot. An indicator counts as "resolved" when *any* source in
    its chain returns a row — even a deep fallback counts, which is what
    you want for the 200-indicator health check.
    """
    if Repository is None:
        return CoverageReport(total=len(MACRO_TIER_A), resolved=0)
    r = repo or Repository(owner_id=owner_id)
    total = len(MACRO_TIER_A)
    resolved = 0
    unresolved: List[str] = []
    by_source: Dict[str, int] = {}
    by_rank: Dict[int, int] = {}
    for name in MACRO_TIER_A.keys():
        obs = pick_indicator(name, owner_id=owner_id, repo=r)
        if obs is None:
            unresolved.append(name)
            continue
        resolved += 1
        by_source[obs.source_id] = by_source.get(obs.source_id, 0) + 1
        by_rank[obs.fallback_rank] = by_rank.get(obs.fallback_rank, 0) + 1
    return CoverageReport(
        total=total,
        resolved=resolved,
        unresolved=unresolved,
        by_source=by_source,
        by_fallback_rank=by_rank,
    )
