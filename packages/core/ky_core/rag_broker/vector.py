"""Dense vector retrieval for broker/research-report RAG.

The vector index is built by ``scripts/build_rag_broker_vec.py`` from the
existing TF-IDF broker chunks. Vectors are normalized, so search is a dot
product against a normalized query embedding.
"""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_VECTOR_DIR = Path.home() / ".ky-platform" / "data" / "rag_broker_vec"
DEFAULT_MODEL = "BAAI/bge-m3"


class BrokerReportVectorRetriever:
    def __init__(self, index_dir: Optional[Path] = None) -> None:
        self.index_dir = Path(index_dir) if index_dir else DEFAULT_VECTOR_DIR
        self._loaded = False
        self._lock = threading.Lock()
        self._vectors: Optional[np.ndarray] = None
        self._chunks: List[Dict[str, Any]] = []
        self._meta: Optional[dict] = None
        self._model = None

    def is_ready(self) -> bool:
        return (self.index_dir / "vectors.npy").is_file() and (
            self.index_dir / "chunks.jsonl"
        ).is_file()

    def meta(self) -> Optional[dict]:
        if self._meta is None:
            path = self.index_dir / "meta.json"
            if path.is_file():
                self._meta = json.loads(path.read_text(encoding="utf-8"))
        return self._meta

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            if not self.is_ready():
                raise FileNotFoundError(f"broker vector index not found at {self.index_dir}")
            self._vectors = np.load(self.index_dir / "vectors.npy", mmap_mode="r")
            chunks: List[Dict[str, Any]] = []
            with (self.index_dir / "chunks.jsonl").open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        chunks.append(json.loads(line))
            self._chunks = chunks
            self._meta = self.meta() or {}
            self._loaded = True
            logger.info(
                "broker vector RAG loaded: %d vectors, model=%s",
                len(self._chunks),
                self._meta.get("model"),
            )

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        meta = self.meta() or {}
        model_name = meta.get("model") or DEFAULT_MODEL
        device = meta.get("device") or "cuda"
        try:
            import torch
            from sentence_transformers import SentenceTransformer
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("sentence_transformers and torch are required") from exc
        if str(device).startswith("cuda") and torch.cuda.is_available():
            try:
                torch.set_float32_matmul_precision("high")
                torch.backends.cuda.matmul.allow_tf32 = True
            except Exception:
                pass
        model = SentenceTransformer(model_name, device=device)
        max_seq_length = meta.get("max_seq_length")
        if max_seq_length:
            model.max_seq_length = int(max_seq_length)
        if str(device).startswith("cuda") and torch.cuda.is_available():
            try:
                model.half()
            except Exception as exc:  # noqa: BLE001
                logger.info("model.half() skipped: %s", exc)
        self._model = model
        return model

    def _embed_query(self, query: str) -> np.ndarray:
        model = self._ensure_model()
        meta = self.meta() or {}
        device = meta.get("device") or "cuda"
        vec = model.encode(
            [query],
            batch_size=1,
            convert_to_numpy=True,
            normalize_embeddings=True,
            device=device,
        )
        return np.asarray(vec[0], dtype=np.float32)

    def search(
        self,
        query: str,
        top_k: int = 5,
        *,
        category: Optional[str] = None,
        broker: Optional[str] = None,
        symbol: Optional[str] = None,
        min_score: float = -1.0,
        text_preview_chars: int = 700,
    ) -> List[Dict[str, Any]]:
        if not query or not query.strip() or top_k <= 0:
            return []
        self._ensure_loaded()
        assert self._vectors is not None

        q_vec = self._embed_query(query)
        scores = self._vectors @ q_vec
        if scores.size == 0:
            return []

        fetch_k = min(max(top_k * 16, 80), scores.size)
        part_idx = np.argpartition(-scores, fetch_k - 1)[:fetch_k]
        order = part_idx[np.argsort(-scores[part_idx])]

        out: List[Dict[str, Any]] = []
        category_norm = category.lower() if category else None
        broker_norm = broker.lower() if broker else None
        symbol_norm = symbol.lower() if symbol else None

        for idx in order:
            i = int(idx)
            score = float(scores[i])
            if score < min_score:
                continue
            rec = self._chunks[i]
            if category_norm and str(rec.get("report_category", "")).lower() != category_norm:
                continue
            if broker_norm and broker_norm not in str(rec.get("broker", "")).lower():
                continue
            if symbol_norm and symbol_norm not in str(rec.get("symbol", "")).lower():
                continue

            item = dict(rec)
            text = str(item.get("text") or "")
            if text_preview_chars and len(text) > text_preview_chars:
                item["text"] = text[:text_preview_chars].rstrip() + "..."
            item["score"] = round(score, 6)
            item["source_type"] = "broker_report"
            item["retrieval"] = "dense"
            out.append(item)
            if len(out) >= top_k:
                break
        return out


_DEFAULT: Optional[BrokerReportVectorRetriever] = None
_DEFAULT_LOCK = threading.Lock()


def _get_default() -> BrokerReportVectorRetriever:
    global _DEFAULT
    if _DEFAULT is None:
        with _DEFAULT_LOCK:
            if _DEFAULT is None:
                _DEFAULT = BrokerReportVectorRetriever()
    return _DEFAULT


def get_broker_vector_retriever() -> BrokerReportVectorRetriever:
    return _get_default()


def search_broker_report_vectors(query: str, top_k: int = 5, **filters: Any) -> List[Dict[str, Any]]:
    try:
        r = _get_default()
        if not r.is_ready():
            return []
        return r.search(query, top_k=top_k, **filters)
    except Exception as exc:  # noqa: BLE001
        logger.warning("broker vector search failed: %s", exc)
        return []
