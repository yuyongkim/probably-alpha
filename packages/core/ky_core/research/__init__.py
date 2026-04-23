"""ky_core.research — knowledge filters + academic factor studies + live data feeds.

Sub-modules
-----------
- :mod:`buffett`        : filter RAG retrieval to Buffett / Berkshire letters.
- :mod:`rag_filters`    : generic RAG topic filters (wizards / psychology / cycles).
- :mod:`fama_french`    : simple SMB / HML / UMD factor returns over the store.
- :mod:`news`           : Naver news search + keyword sentiment.
- :mod:`krreports`      : Korean brokerage reports (Naver Finance scrape).
- :mod:`review`         : weekly / monthly aggregated review (on-demand).
- :mod:`ai_agent`       : Claude-backed Q&A with RAG context (stub fallback).
"""
from __future__ import annotations

from .buffett import BuffettIndex, list_buffett_works, search_buffett
from .fama_french import FactorResult, compute_factor_returns
from .rag_filters import FILTERS, FilterIndex, RagFilter, list_filter_works, search_filter

__all__ = [
    "BuffettIndex",
    "FactorResult",
    "FilterIndex",
    "RagFilter",
    "FILTERS",
    "compute_factor_returns",
    "list_buffett_works",
    "list_filter_works",
    "search_buffett",
    "search_filter",
]
