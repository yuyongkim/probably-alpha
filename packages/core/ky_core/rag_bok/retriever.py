"""BGE-M3 + numpy retriever for BOK reports index.

Loads vectors via mmap (lazy) + chunk records once (1.2GB, kept in RAM). Query
embedding goes through Ollama /api/embed with num_ctx=8192 to match the build.

Cosine similarity is plain `(vectors @ q_vec) / (norms * q_norm)`; for 367K
vectors at 1024 dim this runs in ~100-200 ms on CPU — fine for interactive use.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import requests

log = logging.getLogger(__name__)

DEFAULT_INDEX_DIR = Path.home() / ".ky-platform" / "data" / "rag_bok"
OLLAMA_URL = os.getenv("KY_OLLAMA_URL", "http://localhost:11434/api/embed")
EMBED_MODEL = os.getenv("KY_BGE_MODEL", "bge-m3")
EMBED_DIM = 1024

_SINGLETON: Optional["BOKRetriever"] = None


class BOKRetriever:
    def __init__(self, index_dir: Path = DEFAULT_INDEX_DIR) -> None:
        self.index_dir = Path(index_dir)
        self._vectors: Optional[np.ndarray] = None
        self._chunks: Optional[List[Dict[str, Any]]] = None
        self._norms: Optional[np.ndarray] = None

    def is_ready(self) -> bool:
        return (self.index_dir / "vectors.npy").is_file() and \
               (self.index_dir / "chunks.jsonl").is_file()

    def _ensure_loaded(self) -> None:
        if self._vectors is not None:
            return
        if not self.is_ready():
            raise FileNotFoundError(f"BOK index not found at {self.index_dir}")
        # mmap the vectors so startup is cheap — only rows we access are faulted in
        self._vectors = np.load(self.index_dir / "vectors.npy", mmap_mode="r")
        # Load chunk records once — 1.2GB but needed for top-k lookups
        chunks: List[Dict[str, Any]] = []
        with (self.index_dir / "chunks.jsonl").open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
        self._chunks = chunks
        # Pre-compute L2 norms for cosine similarity
        norms = np.linalg.norm(self._vectors, axis=1)
        norms[norms == 0] = 1.0
        self._norms = norms
        log.info(
            "BOK retriever loaded: %d vectors (%.1fMB mmap), %d chunks",
            self._vectors.shape[0],
            self._vectors.nbytes / 1e6,
            len(chunks),
        )

    def _embed_query(self, query: str) -> np.ndarray:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": EMBED_MODEL,
                "input": query,
                "options": {"num_ctx": 8192},
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        embs = data.get("embeddings") or []
        if not embs:
            raise RuntimeError("empty embeddings from Ollama")
        return np.asarray(embs[0], dtype=np.float32)

    def search(
        self,
        query: str,
        top_k: int = 5,
        *,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        assert self._vectors is not None and self._chunks is not None and self._norms is not None

        q_vec = self._embed_query(query)
        q_norm = float(np.linalg.norm(q_vec) or 1.0)
        # cosine = (V @ q) / (||V|| * ||q||)
        scores = (self._vectors @ q_vec) / (self._norms * q_norm)

        # Optional filters
        mask: Optional[np.ndarray] = None
        if year_min or year_max or category:
            sel = np.ones(len(self._chunks), dtype=bool)
            for i, rec in enumerate(self._chunks):
                y = rec.get("year")
                try:
                    y_int = int(y) if y else None
                except Exception:
                    y_int = None
                if year_min and (y_int is None or y_int < year_min):
                    sel[i] = False
                    continue
                if year_max and (y_int is None or y_int > year_max):
                    sel[i] = False
                    continue
                if category and (rec.get("category") or "") != category:
                    sel[i] = False
            mask = sel

        if mask is not None:
            scores = np.where(mask, scores, -np.inf)

        k = min(top_k, len(scores))
        if k <= 0:
            return []
        top_idx = np.argpartition(-scores, k - 1)[:k]
        top_idx = top_idx[np.argsort(-scores[top_idx])]

        out: List[Dict[str, Any]] = []
        for idx in top_idx:
            i = int(idx)
            if scores[i] == -np.inf:
                continue
            rec = dict(self._chunks[i])
            rec["score"] = float(scores[i])
            rec["source_type"] = rec.get("source_type") or "bok_report"
            out.append(rec)
        return out


def get_retriever() -> BOKRetriever:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = BOKRetriever()
    return _SINGLETON


def search_bok(query: str, top_k: int = 5, **filters: Any) -> List[Dict[str, Any]]:
    """Safe wrapper — returns [] when index missing or Ollama unreachable."""
    try:
        r = get_retriever()
        if not r.is_ready():
            return []
        return r.search(query, top_k=top_k, **filters)
    except Exception as exc:  # noqa: BLE001
        log.warning("BOK search failed: %s", exc)
        return []
