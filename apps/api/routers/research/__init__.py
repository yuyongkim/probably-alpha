"""Research router — 논문 / 리포트 / 매크로 / 지식 베이스 / 버핏 / 팩터 /
RAG 필터 (interviews/psychology/cycles/blogs) / news / krreports / review / ai_agent."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

# Make packages/core importable without requiring `pip install -e .`
# (same shim as routers/chartist/__init__.py).
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

logger = logging.getLogger(__name__)

router = APIRouter()


def _envelope(data: Any = None, error: Any = None, ok: Optional[bool] = None) -> Dict[str, Any]:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}


# --------------------------------------------------------------------------- #
# RAG retriever (lazy singleton — shared with knowledge search)               #
# --------------------------------------------------------------------------- #

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


# --------------------------------------------------------------------------- #
# Knowledge base                                                              #
# --------------------------------------------------------------------------- #


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
    """Lexical (TF-IDF) search across the knowledge base."""
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


# --------------------------------------------------------------------------- #
# Papers / Buffett / Fama-French                                              #
# --------------------------------------------------------------------------- #


@router.get("/papers")
def papers_index(top_k: int = Query(10, ge=1, le=50)) -> dict:
    """Surface 'paper-like' items from the RAG index via topic search."""
    r = _get_retriever()
    if r is None or not r.is_ready():
        return _envelope({
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
    return _envelope({"papers": items, "note": "heuristic; real paper corpus TBD"})


@router.get("/buffett/index")
def buffett_index() -> dict:
    """Return the catalogue of Buffett / Berkshire works in the RAG index."""
    try:
        from ky_core.research.buffett import list_buffett_works
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    idx = list_buffett_works()
    return _envelope(idx.to_dict())


@router.get("/buffett/search")
def buffett_search(
    q: str = Query(..., min_length=1),
    top_k: int = Query(8, ge=1, le=40),
) -> dict:
    """Search the Buffett / Berkshire slice of the RAG index."""
    try:
        from ky_core.research.buffett import search_buffett
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    hits = search_buffett(q, top_k=top_k)
    return _envelope({"query": q, "results": hits, "count": len(hits)})


@router.get("/ffactor")
def ffactor(
    factor: str = Query("MOM", description="SIZE | MOM | VAL"),
    lookback_days: int = Query(252, ge=30, le=1500),
) -> dict:
    """Return a simple Fama-French-style factor return series."""
    try:
        from ky_core.research.fama_french import FACTORS, compute_factor_returns
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    factor = factor.upper()
    if factor not in FACTORS:
        return _envelope(
            None,
            error={"code": "BAD_FACTOR", "message": f"factor must be one of {list(FACTORS)}"},
            ok=False,
        )
    try:
        res = compute_factor_returns(factor, lookback_days=lookback_days)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ffactor compute failed")
        return _envelope(None, error={"code": "COMPUTE_FAILED", "message": str(exc)}, ok=False)
    return _envelope(res.to_dict())


# --------------------------------------------------------------------------- #
# RAG topic filters — interviews / psychology / cycles / blogs                #
# --------------------------------------------------------------------------- #

_RAG_FILTER_SLUGS = {"interviews", "psychology", "cycles", "blogs"}


@router.get("/{slug}/index")
def rag_filter_index(slug: str) -> dict:
    """Catalogue of works inside a RAG topic filter (chunks per work)."""
    if slug not in _RAG_FILTER_SLUGS:
        return _envelope(None, error={"code": "NOT_FOUND", "message": slug}, ok=False)
    try:
        from ky_core.research.rag_filters import list_filter_works
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    idx = list_filter_works(slug)
    return _envelope(idx.to_dict())


@router.get("/{slug}/search")
def rag_filter_search(
    slug: str,
    q: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=40),
) -> dict:
    """TF-IDF search restricted to the named topic filter."""
    if slug not in _RAG_FILTER_SLUGS:
        return _envelope(None, error={"code": "NOT_FOUND", "message": slug}, ok=False)
    try:
        from ky_core.research.rag_filters import search_filter
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    hits = search_filter(slug, q, top_k=top_k)
    return _envelope({"slug": slug, "query": q, "results": hits, "count": len(hits)})


# --------------------------------------------------------------------------- #
# News (Naver) + KR brokerage reports                                         #
# --------------------------------------------------------------------------- #


@router.get("/news/search")
def news_search(
    q: str = Query(..., min_length=1, description="Korean query e.g. '삼성전자'"),
    display: int = Query(10, ge=1, le=30),
) -> dict:
    try:
        from ky_core.research.news import search_news
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    try:
        payload = search_news(q, display=display)
    except Exception as exc:  # noqa: BLE001
        logger.exception("news search failed for q=%r", q)
        return _envelope(None, error={"code": "NEWS_FAILED", "message": str(exc)}, ok=False)
    return _envelope(payload)


@router.get("/krreports/list")
def krreports_list(
    category: str = Query("company", description="company|industry|market|debriefing|economy"),
    limit: int = Query(20, ge=1, le=60),
) -> dict:
    try:
        from ky_core.research.krreports import list_reports
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    try:
        payload = list_reports(category=category, limit=limit)
    except Exception as exc:  # noqa: BLE001
        logger.exception("krreports list failed for category=%s", category)
        return _envelope(None, error={"code": "REPORTS_FAILED", "message": str(exc)}, ok=False)
    return _envelope(payload)


# --------------------------------------------------------------------------- #
# Review + AI agent                                                           #
# --------------------------------------------------------------------------- #


@router.get("/review/latest")
def review_latest(period: str = Query("weekly", description="weekly|monthly")) -> dict:
    try:
        from ky_core.research.review import build_review
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    try:
        payload = build_review(period=period)
    except Exception as exc:  # noqa: BLE001
        logger.exception("review build failed")
        return _envelope(None, error={"code": "REVIEW_FAILED", "message": str(exc)}, ok=False)
    return _envelope(payload)


@router.get("/airesearch/ask")
def airesearch_ask(
    q: str = Query(..., min_length=1),
    k: int = Query(5, ge=1, le=15),
) -> dict:
    try:
        from ky_core.research.ai_agent import ask
    except Exception as exc:  # noqa: BLE001
        return _envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    try:
        answer = ask(q, k=k)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ai_agent ask failed")
        return _envelope(None, error={"code": "AGENT_FAILED", "message": str(exc)}, ok=False)
    return _envelope(answer.to_dict())


# --------------------------------------------------------------------------- #
# Page shells — generic fallback for any remaining pre-data sections          #
# --------------------------------------------------------------------------- #


@router.get("/shell/{slug}")
def shell(slug: str) -> dict:
    """Generic empty shell for pages awaiting a data source."""
    catalogue: Dict[str, Dict[str, Any]] = {
        "reproduce": {"title": "Reproduce Paper Results", "note": "Phase 4 — papers DSL"},
        "ideas": {"title": "Research Ideas", "note": "localStorage-backed, client only"},
        "signallab": {"title": "Signal Lab", "note": "localStorage-backed, client only"},
        "graveyard": {"title": "Signal Graveyard", "note": "localStorage-backed, client only"},
        "airesearch": {"title": "AI Research", "note": "see GET /research/airesearch/ask"},
        "news": {"title": "뉴스", "note": "see GET /research/news/search"},
        "krreports": {"title": "한국 리포트", "note": "see GET /research/krreports/list"},
        "review": {"title": "리서치 리뷰", "note": "see GET /research/review/latest"},
        "cycles": {"title": "사이클 분석", "note": "see GET /research/cycles/{index,search}"},
        "psychology": {"title": "시장 심리", "note": "see GET /research/psychology/{index,search}"},
        "interviews": {"title": "트레이더 인터뷰", "note": "see GET /research/interviews/{index,search}"},
        "blogs": {"title": "블로그", "note": "no blog corpus ingested yet"},
    }
    entry = catalogue.get(slug)
    if not entry:
        return _envelope(None, error={"code": "NOT_FOUND", "message": slug}, ok=False)
    return _envelope({"slug": slug, **entry, "data": []})
