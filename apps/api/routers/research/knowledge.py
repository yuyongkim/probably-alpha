"""Knowledge-base endpoints — TF-IDF search over the general RAG index."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query

from routers.research._shared import (
    envelope,
    get_retriever,
    logger,
    retriever_import_error,
)

router = APIRouter()


@router.get("/knowledge/status")
def knowledge_status() -> dict:
    """Lightweight status probe for the RAG index."""
    r = get_retriever()
    if r is None:
        return envelope(
            {"ready": False, "reason": "ky_core.rag not importable"},
            error={
                "code": "RAG_IMPORT_FAILED",
                "message": retriever_import_error() or "import failed",
            },
        )
    if not r.is_ready():
        return envelope(
            {
                "ready": False,
                "reason": "index files missing",
                "index_dir": str(r.index_dir),
                "hint": "Run `python scripts/build_rag.py --source knowledge "
                        "--source-path <path>` first.",
            }
        )
    meta = r.meta() or {}
    return envelope(
        {
            "ready": True,
            "index_dir": str(r.index_dir),
            "chunks": meta.get("chunks"),
            "files_indexed": meta.get("files_indexed"),
            "files_total": meta.get("files_total"),
            "built_at": meta.get("built_at"),
            "vocabulary_size": meta.get("vocabulary_size"),
        }
    )


@router.get("/knowledge/search")
def knowledge_search(
    q: str = Query(..., min_length=1, description="search query"),
    top_k: int = Query(5, ge=1, le=50),
) -> dict:
    """Lexical (TF-IDF) search across the knowledge base."""
    r = get_retriever()
    if r is None:
        return envelope(
            {
                "results": [],
                "stale": True,
                "message": "ky_core.rag not importable — install dependencies.",
            },
            error={
                "code": "RAG_IMPORT_FAILED",
                "message": retriever_import_error() or "import failed",
            },
        )

    if not r.is_ready():
        return envelope(
            {
                "results": [],
                "stale": True,
                "message": (
                    "Knowledge index not yet built. Run "
                    "`python scripts/build_rag.py --source knowledge "
                    "--source-path <path>` first."
                ),
            }
        )

    try:
        results = r.search(q, top_k=top_k)
    except Exception as exc:
        logger.exception("knowledge search failed for query=%r", q)
        return envelope(
            None,
            error={
                "code": "SEARCH_FAILED",
                "message": str(exc),
            },
            ok=False,
        )

    meta = r.meta() or {}
    return envelope(
        {
            "query": q,
            "top_k": top_k,
            "results": [res.to_dict() for res in results],
            "index": {
                "chunks": meta.get("chunks"),
                "files_indexed": meta.get("files_indexed"),
                "built_at": meta.get("built_at"),
            },
        }
    )


@router.get("/papers")
def papers_index(top_k: int = Query(10, ge=1, le=50)) -> dict:
    """Surface 'paper-like' items from the RAG index via topic search."""
    r = get_retriever()
    if r is None or not r.is_ready():
        return envelope({
            "papers": [],
            "stale": True,
            "message": "Knowledge index not yet built.",
        })
    aggregated: Dict[str, Dict[str, Any]] = {}
    for query in ("paper abstract", "journal finance", "academic study", "empirical evidence"):
        try:
            hits = r.search(query, top_k=top_k)
        except Exception:
            continue
        for h in hits:
            key = h.source_file
            ent = aggregated.setdefault(key, {
                "source_file": key,
                "estimated_work": h.estimated_work,
                "best_score": 0.0,
                "chunks": 0,
                "sample_text": h.text,
            })
            ent["best_score"] = max(ent["best_score"], float(h.score))
            ent["chunks"] += 1
    items = sorted(aggregated.values(), key=lambda x: -x["best_score"])[:top_k]
    return envelope({"papers": items, "note": "heuristic; real paper corpus TBD"})
