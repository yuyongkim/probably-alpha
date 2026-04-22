"""ky_core.rag — knowledge-base lexical retrieval.

Phase 3: Lexical TF-IDF search over PDFs/TXT in `~/.ky-platform/data/rag/`.
Phase 5+: add semantic embeddings alongside TF-IDF.
"""
from __future__ import annotations

from .models import Chunk, SearchResult
from .retriever import Retriever, default_index_dir, search

__all__ = ["Chunk", "SearchResult", "Retriever", "default_index_dir", "search"]
