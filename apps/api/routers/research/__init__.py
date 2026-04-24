"""Research router — 논문 / 리포트 / 매크로 / 지식 베이스 / 버핏 / 팩터 /
RAG 필터 (interviews/psychology/cycles/blogs) / news / krreports / review / ai_agent.

Structure:
    _shared.py      — envelope, logger, lazy RAG retriever singleton
    knowledge.py    — /knowledge/*, /papers
    broker.py       — /broker/* (status/search + vector/*)
    news_reports.py — /news/search, /krreports/list, /review/latest,
                      /airesearch/ask, /shell/{slug}
    academic.py     — /buffett/*, /ffactor, /{slug}/index, /{slug}/search

Mount order: news_reports BEFORE academic. academic contains
``/{slug}/index`` + ``/{slug}/search`` catch-alls that would otherwise
shadow ``/news/search`` and ``/krreports/list``. The catch-all enforces a
whitelist (_RAG_FILTER_SLUGS = interviews/psychology/cycles/blogs) and
short-circuits unknown slugs with a NOT_FOUND envelope — but because
FastAPI matches the first registered route, that short-circuit ran
BEFORE the real news/krreports handlers got a chance. Placing
news_reports first restores the expected precedence.
"""
from __future__ import annotations

from fastapi import APIRouter

from routers.research.academic import router as _academic_router
from routers.research.broker import router as _broker_router
from routers.research.knowledge import router as _knowledge_router
from routers.research.news_reports import router as _news_reports_router

router = APIRouter()

# Concrete routes first; {slug} catch-alls in academic come LAST.
router.include_router(_knowledge_router)    # /knowledge/*, /papers
router.include_router(_broker_router)       # /broker/*
router.include_router(_news_reports_router) # /news/search, /krreports/list, /review/latest, /airesearch/ask, /shell/{slug}
router.include_router(_academic_router)     # /buffett/*, /ffactor, /{slug}/index, /{slug}/search
