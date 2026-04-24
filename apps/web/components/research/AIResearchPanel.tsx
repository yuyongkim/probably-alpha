"use client";
// AIResearchPanel — Claude-backed Q&A with RAG citations (or stub fallback).
import { useState } from "react";
import { apiBase } from "@/lib/apiBase";
import type { AIAgentResponse } from "@/types/research";

export function AIResearchPanel() {
  const [q, setQ] = useState("");
  const [data, setData] = useState<AIAgentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const url = `${apiBase()}/api/v1/research/airesearch/ask?q=${encodeURIComponent(q)}&k=6`;
      const res = await fetch(url);
      const body = (await res.json()) as {
        ok: boolean;
        data?: AIAgentResponse;
        error?: { message?: string };
      };
      if (!body.ok || !body.data) {
        setError(body.error?.message ?? "ask failed");
        setData(null);
      } else {
        setData(body.data);
      }
    } catch (exc: unknown) {
      setError(String(exc));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div
        className="rounded-md border p-3"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <label className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
          ask the research agent
        </label>
        <textarea
          value={q}
          onChange={(e) => setQ(e.target.value)}
          rows={3}
          placeholder="예: '반도체 섹터가 이번 분기 왜 강한가?' · 'Livermore가 말한 pivotal point는?'"
          className="w-full mt-1 py-2 px-3 rounded bg-transparent border text-sm outline-none"
          style={{ borderColor: "var(--border)" }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              submit();
            }
          }}
        />
        <div className="flex items-center justify-between mt-2 text-[11px] text-[color:var(--fg-muted)]">
          <span>
            mode · <span className="mono">{data?.mode ?? "—"}</span>
            {data?.model ? (
              <span className="ml-1 mono">({data.model})</span>
            ) : null}
            {data?.reason ? (
              <span className="ml-1">· {data.reason}</span>
            ) : null}
          </span>
          <button
            type="button"
            onClick={submit}
            disabled={loading || !q.trim()}
            className="px-3 py-1 rounded border mono"
            style={{
              borderColor: "var(--border)",
              background: "var(--surface-raised)",
              opacity: loading || !q.trim() ? 0.6 : 1,
            }}
          >
            {loading ? "thinking…" : "ask (⌘+Enter)"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="text-xs" style={{ color: "var(--neg)" }}>
          {error}
        </div>
      ) : null}

      {data?.answer ? (
        <div
          className="rounded-md border p-3"
          style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
        >
          <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)] mb-1">
            answer
          </div>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {data.answer}
          </p>
        </div>
      ) : null}

      {data?.citations && data.citations.length > 0 ? (
        <div
          className="rounded-md border p-3"
          style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
        >
          <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)] mb-2">
            citations ({data.citations.length})
          </div>
          <ul className="space-y-2">
            {data.citations.map((c, i) => (
              <li key={c.chunk_id} className="text-[12px]">
                <div className="flex items-baseline justify-between mono text-[color:var(--fg-muted)]">
                  <span className="truncate">
                    [{i}] {c.estimated_work}
                  </span>
                  <span>
                    {c.page_start ? `p.${c.page_start} · ` : ""}score{" "}
                    {c.score.toFixed(3)}
                  </span>
                </div>
                <p className="mt-1 leading-snug line-clamp-3">{c.text}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
