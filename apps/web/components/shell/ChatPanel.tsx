// ChatPanel — slide-up assistant panel, 400×560.
// Wired to POST /api/v1/assistant/chat — returns Claude-backed answers
// grounded in RAG + page context. Falls back to server-side stub mode when
// ANTHROPIC_API_KEY is unset.
"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { useChatFab } from "@/lib/chatFab";
import { SIDEBAR_MAP, getTabFromPathname } from "@/lib/sidebarMap";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8300";

const EXAMPLE_PROMPTS = [
  "오늘 SEPA 통과 종목 중 EPS 성장률 상위 5개는?",
  "반도체 섹터가 5주 연속 1위인 이유는 무엇인가?",
  "한미반도체 VCP 패턴을 Minervini 관점에서 설명해줘",
  "지난 달 손절된 종목들의 공통 실패 요인은?",
  "이번 주 실적 발표 예정 종목 중 Wizard pass 높은 것?",
];

function pathParts(pathname: string): { tab: string | null; subsection: string | null } {
  const tab = getTabFromPathname(pathname);
  if (!tab) return { tab: null, subsection: null };
  const groups = SIDEBAR_MAP[tab];
  for (const g of groups) {
    const found = g.links.find((l) => l.href === pathname);
    if (found) return { tab, subsection: found.label };
  }
  return { tab, subsection: null };
}

function labelForPath(pathname: string): string {
  const { tab, subsection } = pathParts(pathname);
  if (!tab) return "Home";
  return subsection ? `${capitalize(tab)} / ${subsection}` : capitalize(tab);
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

interface Msg {
  role: "user" | "assistant";
  text: string;
}

interface ChatApiResponse {
  ok: boolean;
  data: {
    message: string;
    mode?: string;
    model?: string | null;
    sources?: unknown[];
    reason?: string;
  } | null;
  error: { code?: string; message?: string } | null;
}

export function ChatPanel() {
  const pathname = usePathname() || "/";
  const open = useChatFab((s) => s.open);
  const close = useChatFab((s) => s.closePanel);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      role: "assistant",
      text: "안녕하세요. 현재 페이지 컨텍스트 기반으로 질문에 답할 수 있어요.",
    },
  ]);
  if (!open) return null;
  const context = labelForPath(pathname);
  const { tab, subsection } = pathParts(pathname);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || pending) return;

    const nextMsgs: Msg[] = [...msgs, { role: "user", text: trimmed }];
    setMsgs(nextMsgs);
    setInput("");
    setPending(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/assistant/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: nextMsgs
            .filter((m) => m.role === "user" || m.role === "assistant")
            .slice(-8) // cap history
            .map((m) => ({ role: m.role, content: m.text })),
          context: { tab, subsection, symbol: null },
        }),
      });
      const body = (await res.json()) as ChatApiResponse;
      if (!body.ok || !body.data) {
        throw new Error(body.error?.message ?? "assistant call failed");
      }
      const suffix = body.data.mode === "stub" ? " · stub" : "";
      setMsgs((prev) => [
        ...prev,
        {
          role: "assistant",
          text: body.data!.message + (suffix ? `\n— (${suffix.trim()})` : ""),
        },
      ]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setMsgs((prev) => [
        ...prev,
        { role: "assistant", text: `(오류) ${msg}` },
      ]);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="chat-panel open" role="dialog" aria-label="Alpha assistant">
      <div className="chat-header">
        <h3>Alpha Assistant</h3>
        <button
          type="button"
          className="chat-close"
          onClick={close}
          aria-label="Close chat"
        >
          ✕
        </button>
      </div>
      <div className="chat-context">CONTEXT: {context}</div>
      <div className="chat-body">
        {msgs.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            {m.text}
          </div>
        ))}
        {pending && <div className="chat-msg assistant">…</div>}
        {msgs.length <= 1 && !pending && (
          <div className="chat-examples">
            {EXAMPLE_PROMPTS.map((p) => (
              <button
                type="button"
                key={p}
                className="chat-example"
                onClick={() => send(p)}
              >
                {p}
              </button>
            ))}
          </div>
        )}
      </div>
      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="질문을 입력하세요…"
          aria-label="Chat input"
          disabled={pending}
        />
        <button type="submit" disabled={pending}>
          {pending ? "…" : "Ask"}
        </button>
      </form>
    </div>
  );
}
