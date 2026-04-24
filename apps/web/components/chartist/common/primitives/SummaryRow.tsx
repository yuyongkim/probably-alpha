// SummaryRow primitive — dense 6-card strip.

import { toneColor } from "./helpers";

export interface SummaryCell {
  label: string;
  value: string;
  delta?: string;
  tone?: "pos" | "neg" | "amber" | "neutral";
}

export function SummaryRow({ cells }: { cells: SummaryCell[] }) {
  return (
    <div
      className="summary-row grid gap-px mb-3 border rounded-md overflow-hidden"
      style={{
        background: "var(--border)",
        borderColor: "var(--border)",
        gridTemplateColumns: `repeat(${Math.min(cells.length, 6)}, minmax(0, 1fr))`,
      }}
    >
      {cells.map((c) => (
        <div
          key={c.label}
          className="summary-card px-3 py-2.5"
          style={{ background: "var(--surface)" }}
        >
          <div className="label text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
            {c.label}
          </div>
          <div className="value mono text-[17px] mt-0.5 text-[color:var(--fg)]">
            {c.value}
          </div>
          {c.delta && (
            <div
              className="delta mono text-[10.5px] mt-0.5"
              style={{ color: toneColor(c.tone) }}
            >
              {c.delta}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
