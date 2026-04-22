"""Research router — 논문 / 리포트 / 매크로 / 지식 베이스 검색."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

# Make packages/core importable without requiring `pip install -e .`
# (same shim as routers/chartist/__init__.py).
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

logger = logging.getLogger(__name__)

router = APIRouter()


# --- lazy retriever singleton ----------------------------------------------
#
# We avoid importing ky_core.rag at module import time so that the API process
# boots even when the RAG dependencies aren't installed yet. The first request
# to `/knowledge/search` triggers the import.

_RETRIEVER = None
_RETRIEVER_IMPORT_ERROR: Optional[str] = None


def _get_retriever():
    global _RETRIEVER, _RETRIEVER_IMPORT_ERROR
    if _RETRIEVER is not None:
        return _RETRIEVER
    try:
        from ky_core.rag import Retriever  # type: ignore

        _RETRIEVER = Retriever()
        _RETRIEVER_IMPORT_ERROR = None
    except Exception as exc:  # ImportError or misc
        logger.warning("ky_core.rag import failed: %s", exc)
        _RETRIEVER_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
        _RETRIEVER = None
    return _RETRIEVER


def _envelope(data: Any = None, error: Any = None, ok: Optional[bool] = None) -> Dict[str, Any]:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}


@router.get("/papers")
def papers_index() -> dict:
    return _envelope(
        {"papers": [], "_placeholder": "Coming in Phase 3 (port from Dart_Analysis)"}
    )


@router.get("/knowledge/status")
def knowledge_status() -> dict:
    """Lightweight status probe for the RAG index."""
    r = _get_retriever()
    if r is None:
        return _envelope(
            {"ready": False, "reason": "ky_core.rag not importable"},
            error={
                "code": "RAG_IMPORT_FAILED",
                "message": _RETRIEVER_IMPORT_ERROR or "import failed",
            },
        )
    if not r.is_ready():
        return _envelope(
            {
                "ready": False,
                "reason": "index files missing",
                "index_dir": str(r.index_dir),
                "hint": "Run `python scripts/build_rag.py --source knowledge "
                        "--source-path <path>` first.",
            }
        )
    meta = r.meta() or {}
    return _envelope(
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
    """Lexical (TF-IDF) search across the knowledge base.

    When the index hasn't been built yet, returns
    `{ok: true, data: {results: [], stale: true, message: ...}}` so the UI
    can render a prompt rather than treating it as an error.
    """
    r = _get_retriever()
    if r is None:
        return _envelope(
            {
                "results": [],
                "stale": True,
                "message": "ky_core.rag not importable — install dependencies.",
            },
            error={
                "code": "RAG_IMPORT_FAILED",
                "message": _RETRIEVER_IMPORT_ERROR or "import failed",
            },
        )

    if not r.is_ready():
        return _envelope(
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
        return _envelope(
            None,
            error={
                "code": "SEARCH_FAILED",
                "message": str(exc),
            },
            ok=False,
        )

    meta = r.meta() or {}
    return _envelope(
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
