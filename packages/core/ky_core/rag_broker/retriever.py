"""Query-time retrieval for broker/research-report RAG.

This mirrors :mod:`ky_core.rag.retriever` but returns the richer report metadata
stored in ``chunks.jsonl``: report category, broker, symbol, source URLs, and
publication date.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.sparse import csr_matrix

from ky_core.rag.index import load_chunks_text, load_index, load_meta

logger = logging.getLogger(__name__)


def default_index_dir() -> Path:
    return Path.home() / ".ky-platform" / "data" / "rag_broker"


class BrokerReportRetriever:
    def __init__(self, index_dir: Optional[Path] = None) -> None:
        self.index_dir = Path(index_dir) if index_dir else default_index_dir()
        self._loaded = False
        self._lock = threading.Lock()
        self._vectorizer = None
        self._matrix: Optional[csr_matrix] = None
        self._chunk_ids: List[str] = []
        self._chunk_store: Dict[str, Dict[str, Any]] = {}
        self._meta: Optional[dict] = None

    def is_ready(self) -> bool:
        return (self.index_dir / "index.pkl").is_file() and (
            self.index_dir / "chunks.jsonl"
        ).is_file()

    def meta(self) -> Optional[dict]:
        if self._meta is None:
            self._meta = load_meta(self.index_dir)
        return self._meta

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
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
                "broker RAG loaded: %d chunks, %d vocab",
                len(self._chunk_ids),
                len(getattr(self._vectorizer, "vocabulary_", {})),
            )

    def search(
        self,
        query: str,
        top_k: int = 5,
        *,
        category: Optional[str] = None,
        broker: Optional[str] = None,
        symbol: Optional[str] = None,
        min_score: float = 0.0,
        text_preview_chars: int = 700,
    ) -> List[Dict[str, Any]]:
        if not query or not query.strip() or top_k <= 0:
            return []
        self._ensure_loaded()
        assert self._vectorizer is not None and self._matrix is not None

        q_vec = self._vectorizer.transform([query])
        scores_mat = self._matrix @ q_vec.T
        scores = np.asarray(scores_mat.todense()).ravel()
        if scores.size == 0:
            return []

        fetch_k = min(max(top_k * 12, 60), scores.size)
        part_idx = np.argpartition(-scores, fetch_k - 1)[:fetch_k]
        order = part_idx[np.argsort(-scores[part_idx])]

        out: List[Dict[str, Any]] = []
        category_norm = category.lower() if category else None
        broker_norm = broker.lower() if broker else None
        symbol_norm = symbol.lower() if symbol else None

        for i in order:
            score = float(scores[i])
            if score < min_score:
                continue
            rec = self._chunk_store.get(self._chunk_ids[int(i)])
            if rec is None:
                continue
            if category_norm and str(rec.get("report_category", "")).lower() != category_norm:
                continue
            if broker_norm and broker_norm not in str(rec.get("broker", "")).lower():
                continue
            if symbol_norm and symbol_norm not in str(rec.get("symbol", "")).lower():
                continue

            text = rec.get("text", "")
            if text_preview_chars and len(text) > text_preview_chars:
                text = text[:text_preview_chars].rstrip() + "..."
            item = dict(rec)
            item["text"] = text
            item["score"] = round(score, 6)
            item.setdefault("source_type", "broker_report")
            out.append(item)
            if len(out) >= top_k:
                break
        return out


_DEFAULT: Optional[BrokerReportRetriever] = None
_DEFAULT_LOCK = threading.Lock()


def _get_default() -> BrokerReportRetriever:
    global _DEFAULT
    if _DEFAULT is None:
        with _DEFAULT_LOCK:
            if _DEFAULT is None:
                _DEFAULT = BrokerReportRetriever()
    return _DEFAULT


def search_broker_reports(query: str, top_k: int = 5, **filters: Any) -> List[Dict[str, Any]]:
    try:
        r = _get_default()
        if not r.is_ready():
            return []
        return r.search(query, top_k=top_k, **filters)
    except Exception as exc:  # noqa: BLE001
        logger.warning("broker report search failed: %s", exc)
        return []
