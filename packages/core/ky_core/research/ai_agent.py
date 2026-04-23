"""AI Research Agent — Claude-backed Q&A with RAG context.

The agent's job is narrow:

1. Take a user question.
2. Pull up to ``k`` chunks from the RAG index as context.
3. If ``ANTHROPIC_API_KEY`` is set, call Claude with a short system prompt
   that instructs it to cite chunk ids; otherwise return a deterministic
   stub answer that just reiterates the retrieved passages.

The stub mode keeps the endpoint useful even without a key configured.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

try:
    from ky_core.rag import Retriever  # type: ignore
except Exception:  # pragma: no cover
    Retriever = None  # type: ignore

logger = logging.getLogger(__name__)


DEFAULT_MODEL = "claude-3-5-haiku-20241022"
SYSTEM_PROMPT = (
    "You are a terse research analyst helping a Korean investor. "
    "Answer in the same language as the question (Korean when Korean, "
    "English when English). Ground every claim in the provided context "
    "chunks — cite them inline as [#chunk_index]. If the context does "
    "not cover the question, say so plainly and suggest what data would "
    "help. Never invent numbers or sources."
)


@dataclass
class AgentAnswer:
    question: str
    answer: str
    mode: str  # "claude" | "stub"
    model: Optional[str]
    citations: List[Dict[str, Any]]
    stale: bool = False
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


# --------------------------------------------------------------------------- #
# Context retrieval                                                           #
# --------------------------------------------------------------------------- #


def _gather_context(question: str, k: int) -> List[Dict[str, Any]]:
    if Retriever is None:
        return []
    r = Retriever()
    if not r.is_ready():
        return []
    try:
        hits = r.search(question, top_k=k)
    except Exception as exc:
        logger.warning("ai_agent retrieval failed: %s", exc)
        return []
    return [h.to_dict() for h in hits]


def _format_context(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "(no context retrieved)"
    buf: List[str] = []
    for i, c in enumerate(chunks):
        work = c.get("estimated_work") or c.get("source_file") or "unknown"
        page = c.get("page_start")
        page_s = f" · p.{page}" if page is not None else ""
        text = (c.get("text") or "").strip()
        buf.append(f"[{i}] {work}{page_s}\n{text}\n")
    return "\n".join(buf)


# --------------------------------------------------------------------------- #
# Claude call                                                                 #
# --------------------------------------------------------------------------- #


def _claude_answer(question: str, context: str) -> Optional[str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic  # type: ignore
    except Exception as exc:  # pragma: no cover
        logger.info("anthropic SDK not installed: %s", exc)
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=os.getenv("KY_CLAUDE_MODEL", DEFAULT_MODEL),
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Context chunks:\n{context}\n\n"
                        f"Question: {question}\n\n"
                        "Give a focused answer (<=200 words) with inline [#n] citations."
                    ),
                }
            ],
        )
        parts: List[str] = []
        for block in getattr(msg, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts).strip() or None
    except Exception as exc:
        logger.warning("claude call failed: %s", exc)
        return None


def _stub_answer(question: str, chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return (
            "AI Research Agent is running in stub mode and no RAG context was "
            "available for this question. Set ANTHROPIC_API_KEY and build the "
            "RAG index to enable live Claude answers."
        )
    lines = [
        "Stub mode (no ANTHROPIC_API_KEY). Closest passages from the knowledge base:",
        "",
    ]
    for i, c in enumerate(chunks[:3]):
        work = c.get("estimated_work") or c.get("source_file") or "unknown"
        text = (c.get("text") or "").strip()
        snippet = text[:280] + ("…" if len(text) > 280 else "")
        lines.append(f"[{i}] {work} — {snippet}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Public                                                                      #
# --------------------------------------------------------------------------- #


def ask(question: str, k: int = 5) -> AgentAnswer:
    q = (question or "").strip()
    if not q:
        return AgentAnswer(
            question=q,
            answer="",
            mode="stub",
            model=None,
            citations=[],
            stale=True,
            reason="empty question",
        )
    chunks = _gather_context(q, k=k)
    context = _format_context(chunks)

    claude_text = _claude_answer(q, context)
    if claude_text is not None:
        return AgentAnswer(
            question=q,
            answer=claude_text,
            mode="claude",
            model=os.getenv("KY_CLAUDE_MODEL", DEFAULT_MODEL),
            citations=chunks,
        )

    reason = (
        "ANTHROPIC_API_KEY not set"
        if not os.getenv("ANTHROPIC_API_KEY")
        else "Claude call failed or anthropic SDK missing"
    )
    return AgentAnswer(
        question=q,
        answer=_stub_answer(q, chunks),
        mode="stub",
        model=None,
        citations=chunks,
        stale=True,
        reason=reason,
    )
