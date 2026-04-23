// BuffettTimeline — list of Berkshire / Buffett works in the RAG index.
import type { BuffettIndex } from "@/types/research";

interface Props {
  index: BuffettIndex;
}

function inferYears(work: string): string {
  const m = work.match(/(\d{4})/g);
  if (!m) return "";
  if (m.length === 1) return m[0];
  return `${m[0]}–${m[m.length - 1]}`;
}

export function BuffettTimeline({ index }: Props) {
  if (!index.ready || index.works.length === 0) {
    return (
      <div className="text-xs text-[color:var(--fg-muted)]">
        {index.reason ?? "No Buffett sources indexed yet."}
      </div>
    );
  }
  return (
    <ul className="divide-y" style={{ borderColor: "var(--border-soft)" }}>
      {index.works.map((w) => (
        <li
          key={w.source_file}
          className="py-2 flex items-baseline justify-between gap-4"
        >
          <div className="min-w-0">
            <div className="display text-sm truncate">{w.work}</div>
            <div className="text-[11px] mono text-[color:var(--fg-muted)] truncate">
              {w.source_file}
            </div>
          </div>
          <div className="mono text-[11px] text-right shrink-0 text-[color:var(--fg-muted)]">
            <div>{w.chunks.toLocaleString()} chunks</div>
            <div>{inferYears(w.work) || "—"}</div>
          </div>
        </li>
      ))}
    </ul>
  );
}
