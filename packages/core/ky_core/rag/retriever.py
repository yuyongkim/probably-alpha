"""Query-time retrieval over a persisted TF-IDF index."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import List, Optional

import numpy as np
from scipy.sparse import csr_matrix

from .index import load_chunks_text, load_index, load_meta
from .models import SearchResult

logger = logging.getLogger(__name__)


def default_index_dir() -> Path:
    """`~/.ky-platform/data/rag/` — matches CLAUDE.md / ARCHITECTURE.md."""
    return Path.home() / ".ky-platform" / "data" / "rag"


class Retriever:
    """Lazy, thread-safe wrapper around a pickled TF-IDF index.

    Usage:
        r = Retriever()            # uses default_index_dir()
        r.search("circle of competence", top_k=5)
    """

    def __init__(self, index_dir: Optional[Path] = None) -> None:
        self.index_dir = Path(index_dir) if index_dir else default_index_dir()
        self._loaded = False
        self._lock = threading.Lock()
        self._vectorizer = None
        self._matrix: Optional[csr_matrix] = None
        self._chunk_ids: List[str] = []
        self._chunk_store: dict = {}
        self._meta: Optional[dict] = None

    # --- state ----------------------------------------------------------

    def is_ready(self) -> bool:
        return (self.index_dir / "index.pkl").is_file() and (
            self.index_dir / "chunks.jsonl"
        ).is_file()

    def meta(self) -> Optional[dict]:
        if self._meta is None:
            self._meta = load_meta(self.index_dir)
        return self._meta

    # --- loading --------------------------------------------------------

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            logger.info("loading RAG index from %s", self.index_dir)
            payload = load_index(self.index_dir)
            self._vectorizer = payload["vectorizer"]
            matrix = payload["matrix"]
            if not isinstance(matrix, csr_matrix):
                matrix = csr_matrix(matrix)
            self._matrix = matrix
            self._chunk_ids = list(payload["chunk_ids"])
            self._chunk_store = load_chunks_text(self.index_dir)
            self._meta = load_meta(self.index_dir)
            self._loaded = True
            logger.info(
                "RAG index loaded: %s chunks, %s vocab",
                len(self._chunk_ids),
                len(getattr(self._vectorizer, "vocabulary_", {})),
            )

    # --- query ----------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        *,
        min_score: float = 0.0,
        text_preview_chars: int = 600,
    ) -> List[SearchResult]:
        if not query or not query.strip():
            return []
        if top_k <= 0:
            return []
        self._ensure_loaded()
        assert self._vectorizer is not None and self._matrix is not None

        q_vec = self._vectorizer.transform([query])
        # cosine similarity == dot product since both are l2-normalised
        scores_mat = self._matrix @ q_vec.T  # shape (N, 1)
        scores = np.asarray(scores_mat.todense()).ravel()
        if scores.size == 0:
            return []

        k = min(top_k, scores.size)
        # argpartition for speed on large N, then sort the k winners exactly
        part_idx = np.argpartition(-scores, k - 1)[:k]
        order = part_idx[np.argsort(-scores[part_idx])]

        results: List[SearchResult] = []
        for i in order:
            score = float(scores[i])
            if score < min_score:
                continue
            chunk_id = self._chunk_ids[i]
            rec = self._chunk_store.get(chunk_id)
            if rec is None:
                logger.debug("missing chunk record for id=%s", chunk_id)
                continue
            text = rec.get("text", "")
            if text_preview_chars and len(text) > text_preview_chars:
                text = text[:text_preview_chars].rstrip() + "…"
            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    score=round(score, 6),
                    text=text,
                    source_file=rec.get("source_file", ""),
                    estimated_work=rec.get("estimated_work", ""),
                    chunk_index=int(rec.get("chunk_index", 0)),
                    page_start=rec.get("page_start"),
                    page_end=rec.get("page_end"),
                    estimated_author=rec.get("estimated_author"),
                )
            )
        return results


# --- module-level convenience ------------------------------------------

_DEFAULT_RETRIEVER: Optional[Retriever] = None
_DEFAULT_LOCK = threading.Lock()


def _get_default() -> Retriever:
    global _DEFAULT_RETRIEVER
    if _DEFAULT_RETRIEVER is None:
        with _DEFAULT_LOCK:
            if _DEFAULT_RETRIEVER is None:
                _DEFAULT_RETRIEVER = Retriever()
    return _DEFAULT_RETRIEVER


def search(query: str, top_k: int = 5) -> List[SearchResult]:
    """Convenience wrapper using the default index directory."""
    return _get_default().search(query, top_k=top_k)
