// Execute · WebSocket — live KIS orderbook + tick SSE streams.
// Consumes /api/v1/execute/stream/{orderbook,ticks} via EventSource.
"use client";

import { useState } from "react";

import { OrderbookLive } from "@/components/execute/OrderbookLive";
import { TickLog } from "@/components/execute/TickLog";

const DEFAULT_SYMBOLS = ["005930", "000660", "042700"];

export default function Page() {
  const [symbols, setSymbols] = useState<string[]>(DEFAULT_SYMBOLS);
  const [active, setActive] = useState<string>(DEFAULT_SYMBOLS[0]);
  const [draft, setDraft] = useState("");

  function addSymbol() {
    const cleaned = draft.trim().replace(/[^0-9]/g, "");
    if (!cleaned) return;
    const padded = cleaned.padStart(6, "0");
    if (symbols.includes(padded)) return;
    const next = [...symbols, padded].slice(0, 10); // mirror backend cap
    setSymbols(next);
    setActive(padded);
    setDraft("");
  }

  function removeSymbol(sym: string) {
    const next = symbols.filter((s) => s !== sym);
    setSymbols(next);
    if (active === sym && next.length > 0) setActive(next[0]);
  }

  return (
    <div>
      <div className="breadcrumb">
        Execute <span className="sep">/</span>{" "}
        <span className="current">WebSocket 실시간</span>
      </div>
      <div className="page-header">
        <div className="page-title-group">
          <h1>KIS WebSocket 실시간 시세</h1>
          <div className="page-meta">
            H0STASP0 호가 · H0STCNT0 체결 · SSE fan-out · 최대 10심볼 동시
          </div>
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          flexWrap: "wrap",
          marginBottom: 16,
        }}
      >
        {symbols.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setActive(s)}
            style={{
              padding: "4px 10px",
              border: "1px solid var(--border, #333)",
              background: s === active ? "var(--accent, #444)" : "transparent",
              color: s === active ? "#fff" : "inherit",
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
              fontSize: 12,
              borderRadius: 3,
            }}
          >
            {s}
            <span
              onClick={(evt) => {
                evt.stopPropagation();
                removeSymbol(s);
              }}
              style={{ marginLeft: 8, color: "var(--muted)", cursor: "pointer" }}
              aria-label={`remove ${s}`}
            >
              ×
            </span>
          </button>
        ))}
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="심볼 추가 (예: 035720)"
          onKeyDown={(e) => {
            if (e.key === "Enter") addSymbol();
          }}
          style={{
            padding: "4px 8px",
            border: "1px solid var(--border, #333)",
            background: "transparent",
            color: "inherit",
            fontFamily: "var(--font-mono, monospace)",
            fontSize: 12,
            width: 160,
          }}
        />
        <button
          type="button"
          onClick={addSymbol}
          style={{
            padding: "4px 10px",
            border: "1px solid var(--border, #333)",
            background: "transparent",
            color: "inherit",
            cursor: "pointer",
            fontSize: 12,
          }}
        >
          추가
        </button>
        <span style={{ color: "var(--muted)", fontSize: 12 }}>
          구독 심볼 {symbols.length}/10
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
        <section>
          <h3 style={{ fontSize: 13, marginBottom: 8 }}>호가 10단계 (H0STASP0)</h3>
          <OrderbookLive key={`ob-${active}`} symbol={active} />
        </section>
        <section>
          <h3 style={{ fontSize: 13, marginBottom: 8 }}>
            체결 tick (H0STCNT0 · 최근 15건)
          </h3>
          <TickLog key={`tk-${active}`} symbol={active} />
        </section>
      </div>

      <div style={{ marginTop: 24, fontSize: 11, color: "var(--muted)" }}>
        장 종료 후에는 체결 tick이 0건 수신될 수 있으며 호가는 마지막 스냅샷이
        유지됩니다. KIS는 tr_type=1 구독 / tr_type=2 해제 / PINGPONG 헬스체크를
        전송합니다.
      </div>
    </div>
  );
}
