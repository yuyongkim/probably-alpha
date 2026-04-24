"use client";
// KnowledgeSearch — client component; debounced search against /knowledge/search.
import { useEffect, useState } from "react";
import { apiBase } from "@/lib/apiBase";
import type {
  KnowledgeSearchResponse,
  KnowledgeSearchResult,
  KnowledgeStatus,
} from "@/types/research";

interface Props {
  initialQuery?: string;
  initialStatus?: KnowledgeStatus;
}

export function KnowledgeSearch({ initialQuery = "", initialStatus }: Props) {
  const [q, setQ] = useState(initialQuery);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<KnowledgeSearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [status] = useState(initialStatus);

  useEffect(() => {
    if (!q.trim()) {
      setResults([]);
      return;
    }
    const ctrl = new AbortController();
    const t = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const url = `${apiBase()}/api/v1/research/knowledge/search?q=${encodeURIComponent(q)}&top_k=8`;
        const res = await fetch(url, { signal: ctrl.signal });
        const body = (await res.json()) as {
          ok: boolean;
          data?: KnowledgeSearchResponse;
          error?: { message?: string };
        };
        if (!body.ok || !body.data) {
          setError(body.error?.message ?? "search failed");
          setResults([]);
        } else {
          setResults(body.data.results);
        }
      } catch (exc: unknown) {
        if ((exc as { name?: string }).name !== "AbortError") {
          setError(String(exc));
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
    <div className="space-y-4">
      <div
        className="rounded-md border p-3"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <label className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
          Knowledge query
        </label>
        <input
          type="text"
          placeholder="circle of competence, VCP, Livermore pivot point..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-full mt-1 py-2 px-3 rounded bg-transparent border mono text-sm outline-none"
          style={{ borderColor: "var(--border)" }}
        />
        <div className="flex items-center justify-between mt-2 text-[11px] text-[color:var(--fg-muted)]">
          <span>
            {status?.ready
              ? `${status.chunks?.toLocaleString()} chunks · ${status.files_indexed}/${status.files_total} docs`
              : "index not built yet"}
          </span>
          <span className="mono">{loading ? "searching…" : `${results.length} hits`}</span>
        </div>
      </div>

      {error ? (
        <div className="text-xs" style={{ color: "var(--neg)" }}>
          {error}
        </div>
      ) : null}

      <ul className="space-y-2">
        {results.map((r) => (
          <li
            key={r.chunk_id}
            className="rounded-md border p-3"
            style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
          >
            <div className="flex items-center justify-between text-[11px] mono text-[color:var(--fg-muted)]">
              <span className="truncate">{r.estimated_work}</span>
              <span>score {r.score.toFixed(3)}</span>
            </div>
            <div className="text-[11px] mono text-[color:var(--muted)] mt-0.5">
              {r.source_file}
              {r.page_start ? ` · p.${r.page_start}` : ""}
              {r.chunk_index !== undefined ? ` · chunk ${r.chunk_index}` : ""}
            </div>
            <p className="text-sm mt-2 leading-relaxed">{r.text}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
