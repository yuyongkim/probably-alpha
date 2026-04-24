"""Academic endpoints — Buffett corpus, Fama-French factors, RAG topic filters."""
from __future__ import annotations

from fastapi import APIRouter, Query

from routers.research._shared import envelope, logger

router = APIRouter()

_RAG_FILTER_SLUGS = {"interviews", "psychology", "cycles", "blogs"}


@router.get("/buffett/index")
def buffett_index() -> dict:
    """Return the catalogue of Buffett / Berkshire works in the RAG index."""
    try:
        from ky_core.research.buffett import list_buffett_works
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    idx = list_buffett_works()
    return envelope(idx.to_dict())


@router.get("/buffett/search")
def buffett_search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(8, ge=1, le=40),
) -> dict:
    """Search the Buffett / Berkshire slice of the RAG index."""
    try:
        from ky_core.research.buffett import search_buffett
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    hits = search_buffett(q, top_k=top_k)
    return envelope({"query": q, "results": hits, "count": len(hits)})


@router.get("/ffactor")
def ffactor(
    factor: str = Query("MOM", description="SIZE | MOM | VAL"),
    lookback_days: int = Query(252, ge=30, le=1500),
) -> dict:
    """Return a simple Fama-French-style factor return series."""
    try:
        from ky_core.research.fama_french import FACTORS, compute_factor_returns
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    factor = factor.upper()
    if factor not in FACTORS:
        return envelope(
            None,
            error={"code": "BAD_FACTOR", "message": f"factor must be one of {list(FACTORS)}"},
            ok=False,
        )
    try:
        res = compute_factor_returns(factor, lookback_days=lookback_days)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ffactor compute failed")
        return envelope(None, error={"code": "COMPUTE_FAILED", "message": str(exc)}, ok=False)
    return envelope(res.to_dict())


@router.get("/{slug}/index")
def rag_filter_index(slug: str) -> dict:
    """Catalogue of works inside a RAG topic filter (chunks per work)."""
    if slug not in _RAG_FILTER_SLUGS:
        return envelope(None, error={"code": "NOT_FOUND", "message": slug}, ok=False)
    try:
        from ky_core.research.rag_filters import list_filter_works
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    idx = list_filter_works(slug)
    return envelope(idx.to_dict())


@router.get("/{slug}/search")
def rag_filter_search(
    slug: str,
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=40),
) -> dict:
    """TF-IDF search restricted to the named topic filter."""
    if slug not in _RAG_FILTER_SLUGS:
        return envelope(None, error={"code": "NOT_FOUND", "message": slug}, ok=False)
    try:
        from ky_core.research.rag_filters import search_filter
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    hits = search_filter(slug, q, top_k=top_k)
    return envelope({"slug": slug, "query": q, "results": hits, "count": len(hits)})
