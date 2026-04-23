"""Generic RAG filter helpers over ``~/.ky-platform/data/rag/``.

The RAG index already holds 41K+ chunks across 130+ trading / investing
books.  This module provides lightweight *topic filters* so individual
research sub-sections (Wizards interviews, Trading psychology, Market
cycles, Investment blogs) can reuse the same TF-IDF index without
rebuilding it.

Each filter is a tuple of (slug, display_name, match_tokens).  A result
passes the filter if *any* token is a case-insensitive substring of the
chunk's ``source_file`` or ``estimated_work`` field.

Public surface
--------------
- :data:`FILTERS` — registry mapping slug -> :class:`RagFilter`.
- :func:`list_filter_works` — catalogue of works inside a given filter.
- :func:`search_filter` — RAG search with post-filter + over-fetch.

All failure modes are soft: missing index returns empty results with a
``reason`` string the router can surface.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from ky_core.rag import Retriever  # type: ignore
except Exception:  # pragma: no cover
    Retriever = None  # type: ignore


# --------------------------------------------------------------------------- #
# Filter registry                                                             #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RagFilter:
    slug: str
    display: str
    tokens: Tuple[str, ...]

    def matches(self, source_file: str, estimated_work: str = "") -> bool:
        haystack = f"{source_file} {estimated_work}".lower()
        return any(tok in haystack for tok in self.tokens)


#: Registered filters.  Tokens are matched case-insensitively against the
#: chunk's ``source_file`` / ``estimated_work`` strings.  The token lists are
#: derived from the actual titles in the shipped RAG index — see
#: ``~/.ky-platform/data/rag/chunks.jsonl``.
FILTERS: Dict[str, RagFilter] = {
    "interviews": RagFilter(
        slug="interviews",
        display="Wizards Interviews",
        tokens=(
            "market wizards",
            "new market wizards",
            "stock market wizards",
            "reminiscences",
            "livermore",
            "turtle",
            "alchemy of finance",
            "liar",  # Liar's Poker
            "when genius failed",
            "boomerang",
        ),
    ),
    "psychology": RagFilter(
        slug="psychology",
        display="Trading Psychology",
        tokens=(
            "psychology",
            "trading in the zone",
            "disciplined trader",
            "trading for a living",
            "fooled by randomness",
            "irrational exuberance",
            "kahneman",
            "van tharp",
            "discipline",
        ),
    ),
    "cycles": RagFilter(
        slug="cycles",
        display="Market Cycles",
        tokens=(
            "cycle",
            "bubble",
            "extraordinary popular",
            "madness of crowds",
            "mania",
            "crash",
            "irrational exuberance",
            "when genius failed",
            "fooled by randomness",
        ),
    ),
    "blogs": RagFilter(
        slug="blogs",
        display="Investment Blogs",
        # No blog corpus ingested yet — the filter intentionally matches no
        # shipped titles so the endpoint surfaces an empty state + TODO.
        tokens=("__no_blogs_indexed__",),
    ),
}


def _chunks_path() -> Path:
    return Path.home() / ".ky-platform" / "data" / "rag" / "chunks.jsonl"


# --------------------------------------------------------------------------- #
# Catalogue                                                                   #
# --------------------------------------------------------------------------- #


@dataclass
class FilterIndex:
    slug: str
    display: str
    works: List[Dict[str, Any]] = field(default_factory=list)
    total_chunks: int = 0
    ready: bool = False
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slug": self.slug,
            "display": self.display,
            "works": self.works,
            "total_chunks": self.total_chunks,
            "ready": self.ready,
            "reason": self.reason,
        }


def list_filter_works(slug: str) -> FilterIndex:
    """Scan ``chunks.jsonl`` once and build the per-filter catalogue."""
    f = FILTERS.get(slug)
    if f is None:
        return FilterIndex(
            slug=slug, display=slug, ready=False, reason=f"unknown filter: {slug}"
        )
    p = _chunks_path()
    if not p.is_file():
        return FilterIndex(
            slug=slug,
            display=f.display,
            ready=False,
            reason="RAG index not built (chunks.jsonl missing)",
        )

    by_work: Dict[str, Dict[str, Any]] = {}
    total = 0
    try:
        with p.open("r", encoding="utf-8") as fp:
            for line in fp:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                src = rec.get("source_file", "")
                work = rec.get("estimated_work") or src
                if not f.matches(src, work):
                    continue
                total += 1
                entry = by_work.setdefault(
                    work,
                    {
                        "work": work,
                        "source_file": src,
                        "chunks": 0,
                        "pages_min": None,
                        "pages_max": None,
                    },
                )
                entry["chunks"] += 1
                ps = rec.get("page_start")
                pe = rec.get("page_end")
                if ps is not None:
                    entry["pages_min"] = (
                        ps if entry["pages_min"] is None else min(entry["pages_min"], ps)
                    )
                if pe is not None:
                    entry["pages_max"] = (
                        pe if entry["pages_max"] is None else max(entry["pages_max"], pe)
                    )
    except Exception as exc:
        return FilterIndex(
            slug=slug, display=f.display, ready=False, reason=f"scan failed: {exc}"
        )

    works = sorted(by_work.values(), key=lambda w: (-w["chunks"], str(w["work"]).lower()))
    return FilterIndex(
        slug=slug,
        display=f.display,
        works=works,
        total_chunks=total,
        ready=True,
    )


# --------------------------------------------------------------------------- #
# Search                                                                      #
# --------------------------------------------------------------------------- #


def search_filter(slug: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Run a TF-IDF search, then post-filter to keep only in-slug sources."""
    f = FILTERS.get(slug)
    if f is None or Retriever is None:
        return []
    if not query or not query.strip():
        return []
    r = Retriever()
    if not r.is_ready():
        return []
    try:
        raw = r.search(query, top_k=max(top_k * 6, 30))
    except Exception:
        return []
    out: List[Dict[str, Any]] = []
    for res in raw:
        if not f.matches(res.source_file, getattr(res, "estimated_work", "") or ""):
            continue
        out.append(res.to_dict())
        if len(out) >= top_k:
            break
    return out
