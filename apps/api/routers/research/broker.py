"""Broker-report RAG endpoints — Drive-primary lexical + GPU vector indexes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from routers.research._shared import envelope, logger

router = APIRouter()


@router.get("/broker/status")
def broker_status() -> dict:
    """Status for the Drive-first broker report RAG index."""
    try:
        from ky_core.rag_broker import BrokerReportRetriever
    except Exception as exc:  # noqa: BLE001
        return envelope(
            {"ready": False, "reason": "ky_core.rag_broker not importable"},
            error={"code": "BROKER_RAG_IMPORT_FAILED", "message": str(exc)},
        )
    r = BrokerReportRetriever()
    if not r.is_ready():
        return envelope(
            {
                "ready": False,
                "reason": "index files missing",
                "index_dir": str(r.index_dir),
                "source_policy": "Google Drive primary; Naver Finance is fallback metadata/listing only.",
                "hint": "Run `python scripts/build_rag_broker.py --source-path <local-drive-export>`.",
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
            "drive_folder_url": meta.get("drive_folder_url"),
            "source_policy": "Google Drive primary; Naver Finance is fallback metadata/listing only.",
        }
    )


@router.get("/broker/search")
def broker_search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(8, ge=1, le=50),
    category: Optional[str] = Query(None, description="stock|industry|bond|economic|market|investment"),
    broker: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
) -> dict:
    """Search the local index built from the Google Drive report corpus."""
    try:
        from ky_core.rag_broker import BrokerReportRetriever
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    r = BrokerReportRetriever()
    if not r.is_ready():
        return envelope(
            {
                "query": q,
                "results": [],
                "count": 0,
                "stale": True,
                "message": "Broker report RAG index not built. Drive is the primary corpus.",
            }
        )
    try:
        hits = r.search(q, top_k=top_k, category=category, broker=broker, symbol=symbol)
    except Exception as exc:  # noqa: BLE001
        logger.exception("broker report search failed for q=%r", q)
        return envelope(None, error={"code": "BROKER_SEARCH_FAILED", "message": str(exc)}, ok=False)
    meta = r.meta() or {}
    return envelope(
        {
            "query": q,
            "results": hits,
            "count": len(hits),
            "index": {
                "chunks": meta.get("chunks"),
                "files_indexed": meta.get("files_indexed"),
                "built_at": meta.get("built_at"),
                "drive_folder_url": meta.get("drive_folder_url"),
            },
        }
    )


@router.get("/broker/vector/status")
def broker_vector_status() -> dict:
    """Status for the GPU-built dense broker report RAG index."""
    try:
        from ky_core.rag_broker import BrokerReportVectorRetriever
    except Exception as exc:  # noqa: BLE001
        return envelope(
            {"ready": False, "reason": "ky_core.rag_broker vector not importable"},
            error={"code": "BROKER_VECTOR_IMPORT_FAILED", "message": str(exc)},
        )
    r = BrokerReportVectorRetriever()
    if not r.is_ready():
        return envelope(
            {
                "ready": False,
                "reason": "vector index files missing",
                "index_dir": str(r.index_dir),
                "hint": "Run `python scripts/build_rag_broker_vec.py --device cuda`.",
            }
        )
    meta = r.meta() or {}
    return envelope(
        {
            "ready": True,
            "index_dir": str(r.index_dir),
            "chunks": meta.get("chunks"),
            "vectors_shape": meta.get("vectors_shape"),
            "built_at": meta.get("built_at"),
            "model": meta.get("model"),
            "device": meta.get("device"),
            "source_index": meta.get("source_index"),
        }
    )


@router.get("/broker/vector/search")
def broker_vector_search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(8, ge=1, le=50),
    category: Optional[str] = Query(None, description="stock|industry|bond|economic|market|investment"),
    broker: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
) -> dict:
    """Semantic search over the GPU-built broker report vector index."""
    try:
        from ky_core.rag_broker import get_broker_vector_retriever
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    r = get_broker_vector_retriever()
    if not r.is_ready():
        return envelope(
            {
                "query": q,
                "results": [],
                "count": 0,
                "stale": True,
                "message": "Broker vector RAG index not built.",
            }
        )
    try:
        hits = r.search(q, top_k=top_k, category=category, broker=broker, symbol=symbol)
    except Exception as exc:  # noqa: BLE001
        logger.exception("broker vector search failed for q=%r", q)
        return envelope(None, error={"code": "BROKER_VECTOR_SEARCH_FAILED", "message": str(exc)}, ok=False)
    meta = r.meta() or {}
    return envelope(
        {
            "query": q,
            "results": hits,
            "count": len(hits),
            "index": {
                "chunks": meta.get("chunks"),
                "built_at": meta.get("built_at"),
                "model": meta.get("model"),
                "device": meta.get("device"),
            },
        }
    )
