// Research · Papers — heuristic top-scoring sources for "paper/abstract/academic".
import { fetchEnvelope } from "@/lib/api";
import type { PapersResponse } from "@/types/research";
import { DensePage } from "@/components/shared/DensePage";

export const revalidate = 600;

export default async function PapersPage() {
  const data = await fetchEnvelope<PapersResponse>(
    "/api/v1/research/papers?top_k=12",
  );
  return (
    <DensePage tab="Research" current="논문 / 자료" title="학술 논문 · 리서치 자료" meta={`PAPERS · BOOKS${data.note ? ` · ${data.note}` : ""}`}>
      <ul className="space-y-2">
        {data.papers.map((p) => (
          <li
            key={p.source_file}
            className="rounded-md border p-3"
            style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
          >
            <div className="flex items-baseline justify-between">
              <div className="display text-sm truncate">{p.estimated_work}</div>
              <div className="mono text-[11px] text-[color:var(--fg-muted)]">
                score {p.best_score.toFixed(3)} · {p.chunks} hits
              </div>
            </div>
            <div className="text-[11px] mono text-[color:var(--fg-muted)]">
              {p.source_file}
            </div>
            <p className="text-xs mt-2 leading-relaxed">
              {p.sample_text.slice(0, 240)}…
            </p>
          </li>
        ))}
      </ul>
    </DensePage>
  );
}
