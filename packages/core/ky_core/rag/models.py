"""Typed records for the lexical RAG index."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional


@dataclass(slots=True)
class Chunk:
    """One indexable text chunk, produced by `chunker.chunk_document`.

    chunk_id         globally unique id (e.g. `2013_letter.pdf::0007`)
    source_file      filename only, relative to knowledge root
    source_path      absolute path (for debugging; not serialised)
    estimated_work   best-effort "book name" (filename minus year)
    estimated_author optional author guess from filename heuristics
    chunk_index      0-based sequence within the document
    page_start       PDF page where this chunk starts (1-based) — None for TXT
    page_end         PDF page where this chunk ends (1-based) — None for TXT
    word_count       approximate word count
    text             raw chunk text
    """

    chunk_id: str
    source_file: str
    estimated_work: str
    chunk_index: int
    text: str
    word_count: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    estimated_author: Optional[str] = None
    source_path: Optional[str] = field(default=None, repr=False)

    def to_record(self) -> Dict[str, Any]:
        """Serialisable dict for `chunks.jsonl` (source_path stripped)."""
        d = asdict(self)
        d.pop("source_path", None)
        return d


@dataclass(slots=True)
class SearchResult:
    """One ranked result returned by `retriever.search`."""

    chunk_id: str
    score: float
    text: str
    source_file: str
    estimated_work: str
    chunk_index: int
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    estimated_author: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
