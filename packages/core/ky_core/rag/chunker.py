"""Turn extracted document text into chunks of ~500 words with 100-word overlap.

Word-count is used as a proxy for token count (≈ 1.3x relation for English; close
enough for retrieval purposes — no tokenizer dependency required). For Korean
text, whitespace split under-counts tokens, but TF-IDF retrieval still works on
the same units used at query time.

The chunker is page-aware: when pages are available (PDF), each chunk records
the first and last page it spans. For TXT inputs page numbers are None.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from .extractor import Pages
from .models import Chunk


# --- defaults ---
DEFAULT_TARGET_WORDS = 500
DEFAULT_OVERLAP_WORDS = 100
_MIN_CHUNK_WORDS = 40  # skip trailing micro-chunks

_WS_RE = re.compile(r"[ \t ]+")
_MULTINL_RE = re.compile(r"\n{3,}")


@dataclass(slots=True)
class _PageWord:
    word: str
    page: Optional[int]


def _normalise_text(text: str) -> str:
    """Collapse whitespace runs without losing paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WS_RE.sub(" ", text)
    text = _MULTINL_RE.sub("\n\n", text)
    return text.strip()


def _pages_to_words(pages: Pages) -> List[_PageWord]:
    """Flatten pages into a page-tagged word sequence."""
    out: List[_PageWord] = []
    for page_no, raw in pages:
        cleaned = _normalise_text(raw)
        if not cleaned:
            continue
        for w in cleaned.split():
            out.append(_PageWord(w, page_no))
    return out


def _estimate_work(filename: str) -> str:
    """Strip year suffix / '(1)' / '- annotated' / edition markers to produce a
    readable work title. Best-effort only."""
    name = Path(filename).stem
    # drop trailing " - annotated", " (1)", " edition YYYY", " YYYY"
    name = re.sub(r"\s*-\s*annotated\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    name = re.sub(r"\s*\d{4}\s*$", "", name).strip()
    # Buffett letters special case: `2013_letter` → `Buffett Letter 2013`
    m = re.match(r"^(\d{4})_letter$", name, flags=re.IGNORECASE)
    if m:
        return f"Buffett Letter {m.group(1)}"
    if name.startswith("buffett_") and name.endswith("_letter"):
        year = name.split("_")[1]
        return f"Buffett Letter {year}"
    return name or filename


def _estimate_author(filename: str, work: str) -> Optional[str]:
    """Very light heuristic; returns None when uncertain."""
    lc = filename.lower()
    if "letter" in lc and ("buffett" in lc or re.search(r"^\d{4}_letter", lc)):
        return "Warren Buffett"
    if "minervini" in lc:
        return "Mark Minervini"
    if "van tharp" in lc or "van_tharp" in lc:
        return "Van K. Tharp"
    if "lefèvre" in lc or "lefevre" in lc or "reminiscences of a stock operator" in lc:
        return "Edwin Lefèvre"
    if "alchemy of finance" in lc:
        return "George Soros"
    return None


def chunk_document(
    source_path: Path,
    pages: Pages,
    *,
    target_words: int = DEFAULT_TARGET_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
    knowledge_root: Optional[Path] = None,
) -> List[Chunk]:
    """Chunk one document into overlapping word windows.

    `source_path` is used for metadata (filename, chunk_id prefix). Pages come
    from `extractor.extract_text` and carry optional page numbers.
    """
    if target_words <= 0:
        raise ValueError("target_words must be > 0")
    if overlap_words < 0 or overlap_words >= target_words:
        raise ValueError("overlap_words must be in [0, target_words)")

    words = _pages_to_words(pages)
    if len(words) < _MIN_CHUNK_WORDS:
        return []

    # filename relative to knowledge root when provided, else bare name
    if knowledge_root is not None:
        try:
            source_file = str(source_path.relative_to(knowledge_root)).replace("\\", "/")
        except ValueError:
            source_file = source_path.name
    else:
        source_file = source_path.name

    estimated_work = _estimate_work(source_path.name)
    estimated_author = _estimate_author(source_path.name, estimated_work)

    chunks: List[Chunk] = []
    step = target_words - overlap_words
    idx = 0
    chunk_no = 0
    total = len(words)

    while idx < total:
        window = words[idx : idx + target_words]
        # if this is a trailing tiny window, only emit if it's the very first.
        if len(window) < _MIN_CHUNK_WORDS and chunks:
            break

        text = " ".join(w.word for w in window)
        page_nos = [w.page for w in window if w.page is not None]
        page_start = page_nos[0] if page_nos else None
        page_end = page_nos[-1] if page_nos else None

        chunk_id = f"{source_file}::{chunk_no:05d}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                source_file=source_file,
                estimated_work=estimated_work,
                chunk_index=chunk_no,
                text=text,
                word_count=len(window),
                page_start=page_start,
                page_end=page_end,
                estimated_author=estimated_author,
                source_path=str(source_path),
            )
        )
        chunk_no += 1
        idx += step

    return chunks
