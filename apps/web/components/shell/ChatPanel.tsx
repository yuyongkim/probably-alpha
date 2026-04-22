// ChatPanel — slide-up assistant panel, 400×560.
// Displays the current tab/sub-page as context. No backend wired yet;
// the Ask button echoes a stub assistant reply so the UI shape is real.
"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { useChatFab } from "@/lib/chatFab";
import { SIDEBAR_MAP, getTabFromPathname } from "@/lib/sidebarMap";

const EXAMPLE_PROMPTS = [
  "오늘 SEPA 통과 종목 중 EPS 성장률 상위 5개는?",
  "반도체 섹터가 5주 연속 1위인 이유는 무엇인가?",
  "한미반도체 VCP 패턴을 Minervini 관점에서 설명해줘",
  "지난 달 손절된 종목들의 공통 실패 요인은?",
  "이번 주 실적 발표 예정 종목 중 Wizard pass 높은 것?",
];

function labelForPath(pathname: string): string {
  const tab = getTabFromPathname(pathname);
  if (!tab) return "Home";
  const groups = SIDEBAR_MAP[tab];
  for (const g of groups) {
    const found = g.links.find((l) => l.href === pathname);
    if (found) return `${capitalize(tab)} / ${found.label}`;
  }
  return capitalize(tab);
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

interface Msg {
  role: "user" | "assistant";
  text: string;
}

export function ChatPanel() {
  const pathname = usePathname() || "/";
  const open = useChatFab((s) => s.open);
  const close = useChatFab((s) => s.closePanel);
  const [input, setInput] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      role: "assistant",
      text: "안녕하세요. 현재 페이지 컨텍스트 기반으로 질문에 답할 수 있어요.",
    },
  ]);
  if (!open) return null;
  const context = labelForPath(pathname);

  function send(text: string) {
    if (!text.trim()) return;
    setMsgs((prev) => [
      ...prev,
      { role: "user", text },
      {
        role: "assistant",
        text: "(스텁) 실제 LLM 연결은 다음 스프린트에서 배선됩니다.",
      },
    ]);
    setInput("");
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
        {msgs.length <= 1 && (
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
        />
        <button type="submit">Ask</button>
      </form>
    </div>
  );
}
