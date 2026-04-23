"""Buffett-letters filter over the RAG index.

The main TF-IDF index lives in ``~/.ky-platform/data/rag``. This helper reuses
the :class:`Retriever` but post-filters results whose ``source_file`` contains
"Buffett" / "Berkshire" / "berkshire" / "Snowball" / "Essays of Warren" — i.e.
the 21 years of letters plus the companion works that quote them extensively.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from ky_core.rag import Retriever  # type: ignore
except Exception:  # pragma: no cover
    Retriever = None  # type: ignore


BUFFETT_TOKENS = ("buffett", "berkshire", "snowball", "essays of warren")


def _matches(source_file: str) -> bool:
    s = (source_file or "").lower()
    return any(tok in s for tok in BUFFETT_TOKENS)


# --------------------------------------------------------------------------- #
# Works catalogue                                                             #
# --------------------------------------------------------------------------- #


@dataclass
class BuffettIndex:
    works: List[Dict[str, Any]] = field(default_factory=list)
    total_chunks: int = 0
    ready: bool = False
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "works": self.works,
            "total_chunks": self.total_chunks,
            "ready": self.ready,
            "reason": self.reason,
        }


def _chunks_path() -> Path:
    return Path.home() / ".ky-platform" / "data" / "rag" / "chunks.jsonl"


def list_buffett_works() -> BuffettIndex:
    """Scan chunks.jsonl once to build the Buffett catalogue (works → count)."""
    p = _chunks_path()
    if not p.is_file():
        return BuffettIndex(ready=False, reason="RAG index not built")
    by_work: Dict[str, Dict[str, Any]] = {}
    total = 0
    try:
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                src = rec.get("source_file", "")
                if not _matches(src):
                    continue
                total += 1
                work = rec.get("estimated_work") or src
                by_work.setdefault(work, {
                    "work": work,
                    "source_file": src,
                    "chunks": 0,
                    "pages_min": None,
                    "pages_max": None,
                })
                entry = by_work[work]
                entry["chunks"] += 1
                ps = rec.get("page_start")
                pe = rec.get("page_end")
                if ps is not None:
                    entry["pages_min"] = min(entry["pages_min"] or ps, ps)
                if pe is not None:
                    entry["pages_max"] = max(entry["pages_max"] or pe, pe)
    except Exception as exc:
        return BuffettIndex(ready=False, reason=f"scan failed: {exc}")

    works = sorted(by_work.values(), key=lambda w: (-w["chunks"], w["work"].lower()))
    return BuffettIndex(works=works, total_chunks=total, ready=True)


# --------------------------------------------------------------------------- #
# Search                                                                      #
# --------------------------------------------------------------------------- #


def search_buffett(query: str, top_k: int = 8) -> List[Dict[str, Any]]:
    """Run a TF-IDF search, then keep only Buffett / Berkshire sources."""
    if Retriever is None:
        return []
    if not query or not query.strip():
        return []
    r = Retriever()
    if not r.is_ready():
        return []
    # Over-fetch since we post-filter.
    try:
        raw = r.search(query, top_k=max(top_k * 5, 20))
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for res in raw:
        if not _matches(res.source_file):
            continue
        out.append(res.to_dict())
        if len(out) >= top_k:
            break
    return out
