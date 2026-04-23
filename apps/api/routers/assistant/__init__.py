"""Assistant chat router — ChatPanel backend.

Accepts a short multi-turn conversation plus page-level context
(``tab`` + ``subsection`` + optional ``symbol``) and returns a Claude-backed
answer grounded in:

1. Top-5 chunks from the knowledge RAG index (when built).
2. The caller's current page context (which tab, subsection, symbol).
3. The symbol's FnGuide snapshot + latest OHLCV when a symbol is selected.

When ``ANTHROPIC_API_KEY`` is absent or the anthropic SDK is not installed,
we degrade to a deterministic stub that returns the retrieved passages and
context facts so the UI still proves the round-trip.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

# Make packages/core importable.
_PKG_CORE = Path(__file__).resolve().parents[4] / "packages" / "core"
if str(_PKG_CORE) not in sys.path:
    sys.path.insert(0, str(_PKG_CORE))

log = logging.getLogger(__name__)
router = APIRouter()


DEFAULT_MODEL = "claude-3-5-haiku-20241022"
SYSTEM_PROMPT = (
    "You are Alpha Assistant — a concise research aide embedded in the ky-platform "
    "trading dashboard. Answer in the user's language (Korean if they write Korean, "
    "English if English). Ground every numeric claim in the provided CONTEXT or "
    "KNOWLEDGE BASE sections; cite knowledge chunks inline as [#n]. Never invent "
    "tickers, prices, or ratios. Keep answers under 220 words and use bullet points "
    "when comparing items."
)


# --------------------------------------------------------------------------- #
# Request / response models                                                   #
# --------------------------------------------------------------------------- #


class ChatContext(BaseModel):
    tab: Optional[str] = None
    subsection: Optional[str] = None
    symbol: Optional[str] = None


class ChatMessage(BaseModel):
    role: str = Field(..., description="user | assistant")
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[ChatContext] = None


def _envelope(data: Any = None, error: Any = None, ok: Optional[bool] = None) -> dict:
    if ok is None:
        ok = error is None
    return {"ok": bool(ok), "data": data, "error": error}


# --------------------------------------------------------------------------- #
# Context gathering                                                           #
# --------------------------------------------------------------------------- #


def _last_user_message(messages: List[ChatMessage]) -> str:
    for m in reversed(messages):
        if m.role == "user" and m.content.strip():
            return m.content.strip()
    # Fallback: concatenate whatever we have.
    return " ".join(m.content for m in messages if m.content.strip())


def _gather_rag(query: str, k: int = 5) -> List[Dict[str, Any]]:
    try:
        from ky_core.rag import Retriever  # type: ignore
    except Exception as exc:  # noqa: BLE001
        log.info("assistant: ky_core.rag unavailable (%s)", exc)
        return []
    try:
        r = Retriever()
        if not r.is_ready():
            return []
        hits = r.search(query, top_k=k)
    except Exception as exc:  # noqa: BLE001
        log.warning("assistant: RAG search failed: %s", exc)
        return []
    return [h.to_dict() for h in hits]


def _gather_symbol_context(symbol: str | None) -> Dict[str, Any]:
    if not symbol:
        return {}
    try:
        from ky_core.storage import Repository
        repo = Repository()
    except Exception as exc:  # noqa: BLE001
        log.warning("assistant: storage unavailable: %s", exc)
        return {}
    out: Dict[str, Any] = {"symbol": symbol}
    try:
        uni = repo.get_universe(symbol)
        if uni:
            out["name"] = uni.get("name")
            out["sector"] = uni.get("sector")
            out["market"] = uni.get("market")
    except Exception:  # noqa: BLE001
        pass
    try:
        snap = repo.get_fnguide_snapshot(symbol)
        if snap and snap.get("payload"):
            payload = json.loads(snap["payload"])
            keys = (
                "per", "pbr", "roe", "dividend_yield",
                "market_cap", "eps", "bps",
            )
            out["fnguide"] = {k: payload.get(k) for k in keys if payload.get(k) is not None}
    except Exception:  # noqa: BLE001
        pass
    try:
        ohlcv_rows = repo.get_ohlcv(symbol)
        if ohlcv_rows:
            last5 = ohlcv_rows[-5:]
            out["ohlcv_recent"] = [
                {
                    "date": r["date"],
                    "close": r["close"],
                    "volume": r.get("volume"),
                }
                for r in last5
            ]
    except Exception:  # noqa: BLE001
        pass
    return out


# --------------------------------------------------------------------------- #
# Prompt shaping                                                              #
# --------------------------------------------------------------------------- #


def _format_rag(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return "(knowledge index empty)"
    out: List[str] = []
    for i, c in enumerate(chunks):
        work = c.get("estimated_work") or c.get("source_file") or "unknown"
        page = c.get("page_start")
        page_s = f" · p.{page}" if page is not None else ""
        text = (c.get("text") or "").strip().replace("\n", " ")
        if len(text) > 500:
            text = text[:500] + "…"
        out.append(f"[{i}] {work}{page_s}\n{text}")
    return "\n\n".join(out)


def _format_context(ctx: ChatContext | None, symbol_ctx: Dict[str, Any]) -> str:
    lines: List[str] = []
    if ctx is not None:
        if ctx.tab:
            lines.append(f"- current_tab: {ctx.tab}")
        if ctx.subsection:
            lines.append(f"- current_subsection: {ctx.subsection}")
        if ctx.symbol:
            lines.append(f"- selected_symbol: {ctx.symbol}")
    if symbol_ctx:
        if symbol_ctx.get("name"):
            lines.append(f"- company_name: {symbol_ctx['name']}")
        if symbol_ctx.get("sector"):
            lines.append(f"- sector: {symbol_ctx['sector']}")
        fn = symbol_ctx.get("fnguide") or {}
        if fn:
            keys = ", ".join(f"{k}={v}" for k, v in fn.items())
            lines.append(f"- fnguide_snapshot: {keys}")
        ohlcv = symbol_ctx.get("ohlcv_recent") or []
        if ohlcv:
            tail = "; ".join(f"{r['date']}:{r['close']}" for r in ohlcv)
            lines.append(f"- ohlcv_last_{len(ohlcv)}d: {tail}")
    if not lines:
        return "(no page context provided)"
    return "\n".join(lines)


def _render_history(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    # Claude prefers alternating user/assistant — if the caller only sends
    # user messages, pass them as-is. We filter empties defensively.
    rendered: List[Dict[str, str]] = []
    for m in messages:
        if not m.content.strip():
            continue
        role = "assistant" if m.role == "assistant" else "user"
        rendered.append({"role": role, "content": m.content.strip()})
    return rendered


# --------------------------------------------------------------------------- #
# Claude call                                                                 #
# --------------------------------------------------------------------------- #


def _call_claude(
    history: List[Dict[str, str]],
    rag_block: str,
    ctx_block: str,
) -> Optional[str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic  # type: ignore
    except Exception as exc:  # pragma: no cover
        log.info("assistant: anthropic SDK missing (%s)", exc)
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key)
        # Inject the context block as a leading user message so Claude treats
        # the knowledge as the "world" while the real conversation stays clean.
        injected: List[Dict[str, str]] = [
            {
                "role": "user",
                "content": (
                    f"PAGE CONTEXT:\n{ctx_block}\n\n"
                    f"KNOWLEDGE BASE CHUNKS:\n{rag_block}\n\n"
                    "Use the above as grounding. The next turn is my actual question."
                ),
            },
            {
                "role": "assistant",
                "content": "이해했습니다. 질문해 주세요.",
            },
        ]
        messages = injected + history
        msg = client.messages.create(
            model=os.getenv("KY_CLAUDE_MODEL", DEFAULT_MODEL),
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        parts: List[str] = []
        for block in getattr(msg, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts).strip() or None
    except Exception as exc:  # noqa: BLE001
        log.warning("assistant: Claude call failed: %s", exc)
        return None


def _stub_response(
    question: str,
    chunks: List[Dict[str, Any]],
    ctx_block: str,
) -> str:
    lines = [
        "(스텁 모드 — ANTHROPIC_API_KEY 미설정)",
        "현재 페이지 컨텍스트:",
        ctx_block,
        "",
    ]
    if chunks:
        lines.append("지식 베이스 상위 3개 근접 패시지:")
        for i, c in enumerate(chunks[:3]):
            work = c.get("estimated_work") or c.get("source_file") or "unknown"
            text = (c.get("text") or "").strip().replace("\n", " ")
            if len(text) > 240:
                text = text[:240] + "…"
            lines.append(f"  [{i}] {work} — {text}")
    else:
        lines.append("지식 베이스 인덱스가 비어 있거나 빌드되지 않았습니다.")
    lines.append("")
    lines.append(f"(질문 요약: {question[:120]})")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Route                                                                       #
# --------------------------------------------------------------------------- #


@router.post("/chat")
def chat(req: ChatRequest) -> dict:
    if not req.messages:
        return _envelope(
            None,
            error={"code": "EMPTY", "message": "messages array empty"},
            ok=False,
        )
    question = _last_user_message(req.messages)
    if not question:
        return _envelope(
            None,
            error={"code": "EMPTY", "message": "no user message content"},
            ok=False,
        )

    chunks = _gather_rag(question, k=5)
    symbol_ctx = _gather_symbol_context(req.context.symbol if req.context else None)
    ctx_block = _format_context(req.context, symbol_ctx)
    rag_block = _format_rag(chunks)

    history = _render_history(req.messages)

    claude_text = _call_claude(history, rag_block, ctx_block)
    if claude_text is not None:
        return _envelope(
            {
                "message": claude_text,
                "mode": "claude",
                "model": os.getenv("KY_CLAUDE_MODEL", DEFAULT_MODEL),
                "sources": chunks,
                "context_used": {
                    "tab": req.context.tab if req.context else None,
                    "subsection": req.context.subsection if req.context else None,
                    "symbol": req.context.symbol if req.context else None,
                    "symbol_ctx_keys": sorted(list(symbol_ctx.keys())),
                    "rag_chunks": len(chunks),
                },
            }
        )

    reason = (
        "ANTHROPIC_API_KEY not set"
        if not os.getenv("ANTHROPIC_API_KEY")
        else "Claude call failed or anthropic SDK missing"
    )
    return _envelope(
        {
            "message": _stub_response(question, chunks, ctx_block),
            "mode": "stub",
            "model": None,
            "sources": chunks[:3],
            "reason": reason,
            "context_used": {
                "tab": req.context.tab if req.context else None,
                "subsection": req.context.subsection if req.context else None,
                "symbol": req.context.symbol if req.context else None,
                "rag_chunks": len(chunks),
            },
        }
    )


@router.get("/health")
def health() -> dict:
    """Light probe — reports whether Claude is reachable and RAG is ready."""
    has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    try:
        import anthropic  # noqa: F401  # type: ignore
        sdk_ok = True
    except Exception:  # noqa: BLE001
        sdk_ok = False
    try:
        from ky_core.rag import Retriever  # type: ignore
        ready = Retriever().is_ready()
    except Exception:  # noqa: BLE001
        ready = False
    return _envelope(
        {
            "mode": "claude" if (has_key and sdk_ok) else "stub",
            "anthropic_api_key": has_key,
            "anthropic_sdk": sdk_ok,
            "rag_ready": ready,
            "model": os.getenv("KY_CLAUDE_MODEL", DEFAULT_MODEL),
        }
    )
