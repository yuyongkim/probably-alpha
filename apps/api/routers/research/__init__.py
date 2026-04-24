"""Research router — 논문 / 리포트 / 매크로 / 지식 베이스 / 버핏 / 팩터 /
RAG 필터 (interviews/psychology/cycles/blogs) / news / krreports / review / ai_agent.

Structure:
    _shared.py      — envelope, logger, lazy RAG retriever singleton
    knowledge.py    — /knowledge/*, /papers
    broker.py       — /broker/* (status/search + vector/*)
    academic.py     — /buffett/*, /ffactor, /{slug}/index, /{slug}/search
    news_reports.py — /news/search, /krreports/list, /review/latest,
                      /airesearch/ask, /shell/{slug}

Mount order preserves the original registration order exactly, because
the academic router contains ``/{slug}/index`` + ``/{slug}/search``
catch-alls that were registered BEFORE ``/news/search`` / ``/krreports/list``
in the original file — reordering them would change routing precedence
for paths like ``/api/v1/research/news/search``.
"""
from __future__ import annotations

from fastapi import APIRouter

from routers.research.academic import router as _academic_router
from routers.research.broker import router as _broker_router
from routers.research.knowledge import router as _knowledge_router
from routers.research.news_reports import router as _news_reports_router

router = APIRouter()

# Order matches the original file top-to-bottom to preserve route precedence.
router.include_router(_knowledge_router)    # /knowledge/status, /knowledge/search, /papers
router.include_router(_broker_router)       # /broker/*
router.include_router(_academic_router)     # /buffett/*, /ffactor, /{slug}/index, /{slug}/search
router.include_router(_news_reports_router) # /news/search, /krreports/list, /review/latest, /airesearch/ask, /shell/{slug}
