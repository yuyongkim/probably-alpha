"""FnGuide snapshot endpoint — Naver + comp.fnguide.com fundamentals."""
from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Query

from routers.value._shared import envelope, log

router = APIRouter()

FNGUIDE_CACHE_TTL_SEC = 600  # 10 minutes per symbol


@router.get("/fnguide/{symbol}")
def fnguide_endpoint(
    symbol: str,
    refresh: bool = Query(False, description="force re-fetch ignoring cache"),
) -> dict:
    """Return the cached/fresh FnGuide snapshot for ``symbol``.

    Cache lifetime: 10 minutes. Backing store: ``fnguide_snapshots`` table in
    ky.db. When refresh=true we ignore cache age but still persist so future
    callers benefit.
    """
    try:
        from ky_core.storage import Repository
        repo = Repository()
    except Exception as exc:  # noqa: BLE001
        log.exception("fnguide: repo unavailable")
        return envelope(
            None,
            error={"code": "STORAGE_UNAVAILABLE", "message": str(exc)},
            ok=False,
        )

    cached = repo.get_fnguide_snapshot(symbol)
    if cached and not refresh:
        fetched_iso = cached.get("fetched_at") or ""
        try:
            fetched_dt = datetime.fromisoformat(fetched_iso) if fetched_iso else None
        except ValueError:
            fetched_dt = None
        age = (
            (datetime.utcnow() - fetched_dt).total_seconds()
            if fetched_dt
            else FNGUIDE_CACHE_TTL_SEC + 1
        )
        if age <= FNGUIDE_CACHE_TTL_SEC:
            try:
                payload = json.loads(cached["payload"])
            except Exception:  # noqa: BLE001
                payload = None
            if payload:
                return envelope({
                    **payload,
                    "cached": True,
                    "age_seconds": int(age),
                })

    try:
        from ky_adapters.naver_fnguide import FnguideAdapter
        adapter = FnguideAdapter.from_settings()
        # Enriched bundle: Mobile (integration + finance + trend) + NaverComp
        # (cF3002 / cF4002 / cF9001 / ownership). Runs in-parallel internally.
        snapshot = adapter.get_full_snapshot(symbol)
        adapter.close()
    except Exception as exc:  # noqa: BLE001
        log.exception("fnguide: fetch failed for %s", symbol)
        # Degrade gracefully — if we have *any* cache at all, serve it with a flag.
        if cached:
            try:
                payload = json.loads(cached["payload"])
                return envelope({
                    **payload,
                    "cached": True,
                    "stale": True,
                    "fetch_error": f"{type(exc).__name__}: {exc}",
                })
            except Exception:  # noqa: BLE001
                pass
        return envelope(
            None,
            error={"code": "FNGUIDE_FAILED", "message": str(exc)},
            ok=False,
        )

    payload = snapshot.to_dict()
    try:
        repo.upsert_fnguide_snapshot(
            symbol,
            json.dumps(payload, ensure_ascii=False),
            source=snapshot.source,
            degraded=snapshot.degraded,
        )
    except Exception:  # noqa: BLE001
        log.exception("fnguide: persist failed for %s", symbol)

    return envelope({**payload, "cached": False, "age_seconds": 0})
