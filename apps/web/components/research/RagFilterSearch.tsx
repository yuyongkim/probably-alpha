"use client";
// RagFilterSearch — topic-filtered RAG search (interviews / psychology /
// cycles / blogs).  Mirrors BuffettSearch shape; one component, four slugs.
import { useEffect, useState } from "react";
import { apiBase } from "@/lib/apiBase";
import type {
  KnowledgeSearchResult,
  RagFilterIndex,
  RagFilterSearchResponse,
} from "@/types/research";

interface Props {
  slug: "interviews" | "psychology" | "cycles" | "blogs";
  initialQuery?: string;
  placeholder?: string;
  emptyCopy?: string;
}

export function RagFilterSearch({
  slug,
  initialQuery = "",
  placeholder,
  emptyCopy,
}: Props) {
  const [index, setIndex] = useState<RagFilterIndex | null>(null);
  const [q, setQ] = useState(initialQuery);
  const [hits, setHits] = useState<KnowledgeSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Catalogue --------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch(`${apiBase()}/api/v1/research/${slug}/index`);
        const body = (await r.json()) as {
          ok: boolean;
          data?: RagFilterIndex;
        };
        if (!cancelled && body.ok && body.data) setIndex(body.data);
      } catch {
        /* ignore — index is optional */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  // Search (debounced) -----------------------------------------------------
  useEffect(() => {
    if (!q.trim()) {
      setHits([]);
      return;
    }
    const ctrl = new AbortController();
    const t = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const url = `${apiBase()}/api/v1/research/${slug}/search?q=${encodeURIComponent(q)}&top_k=6`;
        const res = await fetch(url, { signal: ctrl.signal });
        const body = (await res.json()) as {
          ok: boolean;
          data?: RagFilterSearchResponse;
          error?: { message?: string };
        };
        if (!body.ok || !body.data) {
          setError(body.error?.message ?? "search failed");
          setHits([]);
        } else {
          setHits(body.data.results);
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
  }, [q, slug]);

  const totalWorks = index?.works?.length ?? 0;
  const totalChunks = index?.total_chunks ?? 0;
  const isBlogs = slug === "blogs";

  return (
    <div className="space-y-4">
      <div
        className="rounded-md border p-3"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <label className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
          {slug} query
        </label>
        <input
          type="text"
          placeholder={
            placeholder ??
            (isBlogs
              ? "no blog corpus ingested yet"
              : "cut losses, risk of ruin, trend template…")
          }
          value={q}
          onChange={(e) => setQ(e.target.value)}
          disabled={isBlogs && totalChunks === 0}
          className="w-full mt-1 py-2 px-3 rounded bg-transparent border mono text-sm outline-none"
          style={{ borderColor: "var(--border)" }}
        />
        <div className="flex items-center justify-between mt-2 text-[11px] text-[color:var(--fg-muted)]">
          <span>
            {index?.ready
              ? `${totalChunks.toLocaleString()} chunks · ${totalWorks} books`
              : index?.reason ?? "index not built yet"}
          </span>
          <span className="mono">{loading ? "searching…" : `${hits.length} hits`}</span>
        </div>
      </div>

      {isBlogs && totalChunks === 0 ? (
        <div
          className="rounded-md border p-4 text-sm"
          style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
        >
          <div className="font-semibold mb-1">블로그 아카이브 비어 있음</div>
          <p className="text-[color:var(--fg-muted)]">
            {emptyCopy ??
              "투자 블로그 크롤러가 아직 돌지 않았습니다. 수집 후 RAG 인덱스를 재빌드하면 이 검색이 활성화됩니다."}
          </p>
          <button
            type="button"
            disabled
            className="mt-3 px-3 py-1.5 text-xs rounded border mono opacity-60 cursor-not-allowed"
            style={{ borderColor: "var(--border)" }}
            title="TODO: wire blog crawler"
          >
            collect blogs (TODO)
          </button>
        </div>
      ) : null}

      {error ? (
        <div className="text-xs" style={{ color: "var(--neg)" }}>
          {error}
        </div>
      ) : null}

      {index?.works && index.works.length > 0 && hits.length === 0 && q.trim() === "" ? (
        <div
          className="rounded-md border p-3"
          style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
        >
          <div className="text-[11px] uppercase tracking-widest text-[color:var(--muted)] mb-2">
            included books
          </div>
          <ul className="grid grid-cols-1 md:grid-cols-2 gap-1 text-[12px]">
            {index.works.slice(0, 20).map((w) => (
              <li key={w.source_file} className="flex justify-between gap-2">
                <span className="truncate">{w.work}</span>
                <span className="mono text-[color:var(--fg-muted)]">
                  {w.chunks}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <ul className="space-y-2">
        {hits.map((r) => (
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
