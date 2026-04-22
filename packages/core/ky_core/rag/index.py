"""TF-IDF index build + persistence.

We use `sklearn.feature_extraction.text.TfidfVectorizer` with sublinear TF and a
modest max_features cap to keep the pickle small and memory low. The resulting
artefacts are:

- `index.pkl`      — pickle of {"vectorizer", "matrix", "chunk_ids", "version"}
- `chunks.jsonl`   — one JSON chunk record per line (metadata + text)
- `meta.json`      — build manifest (counts, sizes, timestamps)

At search time `retriever.Retriever` lazy-loads these artefacts once.
"""
from __future__ import annotations

import json
import logging
import pickle
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Sequence

from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

from .models import Chunk

logger = logging.getLogger(__name__)

INDEX_FORMAT_VERSION = 1
INDEX_FILENAME = "index.pkl"
CHUNKS_FILENAME = "chunks.jsonl"
META_FILENAME = "meta.json"

# Vectoriser defaults — chosen for English investment literature + Korean mixed.
_MIN_DF = 2
_MAX_DF = 0.95
_MAX_FEATURES = 200_000
_NGRAM_RANGE = (1, 2)


def _make_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        ngram_range=_NGRAM_RANGE,
        min_df=_MIN_DF,
        max_df=_MAX_DF,
        max_features=_MAX_FEATURES,
        sublinear_tf=True,
        norm="l2",
    )


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_chunks_jsonl(chunks: Iterable[Chunk], path: Path) -> int:
    """Stream chunks to a jsonl file. Returns the byte size of the file."""
    _ensure_dir(path.parent)
    count = 0
    with path.open("w", encoding="utf-8") as fh:
        for c in chunks:
            fh.write(json.dumps(c.to_record(), ensure_ascii=False))
            fh.write("\n")
            count += 1
    logger.info("wrote %s chunk records to %s", count, path)
    return count


def build_index(
    chunks: Sequence[Chunk],
    *,
    index_dir: Path,
    source_label: str,
    source_path: str,
    files_total: int,
    files_failed: Sequence[str] = (),
) -> dict:
    """Fit TF-IDF on the supplied chunks, persist all three artefacts, return
    the meta dict that was written to `meta.json`."""
    if not chunks:
        raise ValueError("build_index called with no chunks")

    _ensure_dir(index_dir)
    started = time.time()

    texts = [c.text for c in chunks]
    vectorizer = _make_vectorizer()
    logger.info("fitting TF-IDF on %s chunks...", len(chunks))
    matrix = vectorizer.fit_transform(texts)
    if not isinstance(matrix, csr_matrix):
        matrix = csr_matrix(matrix)
    logger.info("matrix shape: %s, nnz: %s", matrix.shape, matrix.nnz)

    # 1. persist chunks.jsonl
    chunks_path = index_dir / CHUNKS_FILENAME
    write_chunks_jsonl(chunks, chunks_path)

    # 2. persist index.pkl
    index_path = index_dir / INDEX_FILENAME
    chunk_ids = [c.chunk_id for c in chunks]
    payload = {
        "version": INDEX_FORMAT_VERSION,
        "vectorizer": vectorizer,
        "matrix": matrix,
        "chunk_ids": chunk_ids,
    }
    with index_path.open("wb") as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)

    # 3. write meta.json
    meta = {
        "version": INDEX_FORMAT_VERSION,
        "source_label": source_label,
        "source_path": source_path,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "build_seconds": round(time.time() - started, 1),
        "files_total": files_total,
        "files_indexed": files_total - len(files_failed),
        "files_failed": list(files_failed),
        "chunks": len(chunks),
        "vocabulary_size": len(vectorizer.vocabulary_),
        "matrix_nnz": int(matrix.nnz),
        "index_bytes": index_path.stat().st_size,
        "chunks_bytes": chunks_path.stat().st_size,
        "vectorizer": {
            "ngram_range": list(_NGRAM_RANGE),
            "min_df": _MIN_DF,
            "max_df": _MAX_DF,
            "max_features": _MAX_FEATURES,
            "sublinear_tf": True,
            "norm": "l2",
        },
    }
    meta_path = index_dir / META_FILENAME
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("wrote %s", meta_path)
    return meta


def load_index(index_dir: Path) -> dict:
    """Load the pickled index artefact. Raises FileNotFoundError if missing."""
    index_path = index_dir / INDEX_FILENAME
    if not index_path.is_file():
        raise FileNotFoundError(f"index not found at {index_path}")
    with index_path.open("rb") as fh:
        payload = pickle.load(fh)
    if payload.get("version") != INDEX_FORMAT_VERSION:
        logger.warning(
            "index format version mismatch: got %s, expected %s",
            payload.get("version"),
            INDEX_FORMAT_VERSION,
        )
    return payload


def load_meta(index_dir: Path) -> dict | None:
    meta_path = index_dir / META_FILENAME
    if not meta_path.is_file():
        return None
    return json.loads(meta_path.read_text(encoding="utf-8"))


def load_chunks_text(index_dir: Path) -> dict:
    """Load chunks.jsonl into a {chunk_id: record} dict. Streaming-friendly
    enough for ~50k chunks; swap for a mmap'd key index if it grows large."""
    chunks_path = index_dir / CHUNKS_FILENAME
    if not chunks_path.is_file():
        raise FileNotFoundError(f"chunks file not found at {chunks_path}")
    out: dict = {}
    with chunks_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out[rec["chunk_id"]] = rec
    return out
