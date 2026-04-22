// NotesPane — quick trade-journal scratchpad.
// Persists to localStorage per symbol so notes survive reloads.
"use client";

import { useEffect, useState } from "react";

interface Props {
  symbol: string;
}

const KEY = (sym: string) => `ky:notes:${sym}`;

export function NotesPane({ symbol }: Props) {
  const [text, setText] = useState("");
  const [saved, setSaved] = useState<string | null>(null);

  useEffect(() => {
    try {
      const v = window.localStorage.getItem(KEY(symbol));
      setText(v ?? "");
    } catch {
      setText("");
    }
  }, [symbol]);

  function save() {
    try {
      window.localStorage.setItem(KEY(symbol), text);
      setSaved(new Date().toLocaleTimeString());
    } catch {
      setSaved("save failed");
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="text-[11px] text-[color:var(--fg-muted)]">
        매매일지 — {symbol} · 브라우저 로컬에만 저장됩니다
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={14}
        placeholder="진입 사유, 손절선, 타임스탬프 이벤트 등을 자유롭게 기록…"
        className="w-full px-3 py-2 rounded text-[12.5px] leading-relaxed"
        style={{
          background: "var(--bg)",
          border: "1px solid var(--border)",
          color: "var(--fg)",
          fontFamily: "var(--font-sans)",
        }}
      />
      <div className="flex items-center gap-3">
        <button
          onClick={save}
          className="px-3 py-1 rounded text-[11px] font-medium"
          style={{ background: "var(--accent)", color: "var(--bg)" }}
        >
          Save
        </button>
        {saved && (
          <span className="text-[10.5px] text-[color:var(--fg-muted)]">
            저장됨 · {saved}
          </span>
        )}
      </div>
    </div>
  );
}
