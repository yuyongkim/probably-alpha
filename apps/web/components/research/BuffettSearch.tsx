"use client";
// BuffettSearch — Buffett-scoped RAG search (client component).
import { useEffect, useState } from "react";
import { apiBase } from "@/lib/apiBase";
import type { BuffettSearchResponse, KnowledgeSearchResult } from "@/types/research";

export function BuffettSearch() {
  const [q, setQ] = useState("circle of competence");
  const [hits, setHits] = useState<KnowledgeSearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!q.trim()) return;
    const ctrl = new AbortController();
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const url = `${apiBase()}/api/v1/research/buffett/search?q=${encodeURIComponent(q)}&top_k=6`;
        const res = await fetch(url, { signal: ctrl.signal });
        const body = (await res.json()) as {
          ok: boolean;
          data?: BuffettSearchResponse;
        };
        if (body.ok && body.data) {
          setHits(body.data.results);
        }
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => {
      ctrl.abort();
      clearTimeout(t);
    };
  }, [q]);

  return (
    <div className="space-y-3">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        className="w-full py-2 px-3 rounded bg-transparent border mono text-sm outline-none"
        style={{ borderColor: "var(--border)" }}
        placeholder="margin of safety, intrinsic value, circle of competence..."
      />
      <div className="text-[11px] text-[color:var(--fg-muted)] mono">
        {loading ? "searching…" : `${hits.length} hits`}
      </div>
      <ul className="space-y-2">
        {hits.map((h) => (
          <li
            key={h.chunk_id}
            className="rounded-md border p-3"
            style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
          >
            <div className="flex items-baseline justify-between text-[11px] mono text-[color:var(--fg-muted)]">
              <span className="truncate">{h.estimated_work}</span>
              <span>{h.score.toFixed(3)}</span>
            </div>
            <p className="text-sm mt-1 leading-relaxed">{h.text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
