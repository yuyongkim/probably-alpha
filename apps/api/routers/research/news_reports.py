"""News / KR broker reports / review / AI agent / generic page shell."""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query

from routers.research._shared import envelope, logger

router = APIRouter()


@router.get("/news/search")
def news_search(
    q: str = Query(..., min_length=1, description="Korean query e.g. '삼성전자'"),
    display: int = Query(10, ge=1, le=30),
) -> dict:
    try:
        from ky_core.research.news import search_news
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    try:
        payload = search_news(q, display=display)
    except Exception as exc:  # noqa: BLE001
        logger.exception("news search failed for q=%r", q)
        return envelope(None, error={"code": "NEWS_FAILED", "message": str(exc)}, ok=False)
    return envelope(payload)


@router.get("/krreports/list")
def krreports_list(
    category: str = Query("company", description="company|industry|market|debriefing|economy"),
    limit: int = Query(20, ge=1, le=60),
) -> dict:
    try:
        from ky_core.research.krreports import list_reports
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    try:
        payload = list_reports(category=category, limit=limit)
    except Exception as exc:  # noqa: BLE001
        logger.exception("krreports list failed for category=%s", category)
        return envelope(None, error={"code": "REPORTS_FAILED", "message": str(exc)}, ok=False)
    return envelope(payload)


@router.get("/review/latest")
def review_latest(period: str = Query("weekly", description="weekly|monthly")) -> dict:
    try:
        from ky_core.research.review import build_review
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    try:
        payload = build_review(period=period)
    except Exception as exc:  # noqa: BLE001
        logger.exception("review build failed")
        return envelope(None, error={"code": "REVIEW_FAILED", "message": str(exc)}, ok=False)
    return envelope(payload)


@router.get("/airesearch/ask")
def airesearch_ask(
    q: str = Query(..., min_length=1),
    k: int = Query(5, ge=1, le=15),
) -> dict:
    try:
        from ky_core.research.ai_agent import ask
    except Exception as exc:  # noqa: BLE001
        return envelope(None, error={"code": "IMPORT_FAILED", "message": str(exc)}, ok=False)
    try:
        answer = ask(q, k=k)
    except Exception as exc:  # noqa: BLE001
        logger.exception("ai_agent ask failed")
        return envelope(None, error={"code": "AGENT_FAILED", "message": str(exc)}, ok=False)
    return envelope(answer.to_dict())


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
        return envelope(None, error={"code": "NOT_FOUND", "message": slug}, ok=False)
    return envelope({"slug": slug, **entry, "data": []})
