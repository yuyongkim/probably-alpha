// SummaryRow — a one-line editorial summary block used at the top of most pages.
// Keep this component presentational; data comes from hooks.
// Target ≤ 60 lines (CONTRIBUTING §1).
import type { JSX } from "react";

export interface SummaryCell {
  label: string;
  value: string | number;
  delta?: number;        // signed number; color coded
  suffix?: string;       // e.g. "%", "억", "x"
  tone?: "pos" | "neg" | "neutral";
}

export interface SummaryRowProps {
  cells: SummaryCell[];
  as?: keyof JSX.IntrinsicElements;
  dense?: boolean;
}

export function SummaryRow({ cells, as: Tag = "div", dense = false }: SummaryRowProps) {
  return (
    <Tag
      className={[
        "grid gap-6 border-b border-border pb-3",
        dense ? "grid-cols-4 md:grid-cols-6" : "grid-cols-2 md:grid-cols-4",
      ].join(" ")}
    >
      {cells.map((c) => (
        <div key={c.label} className="min-w-0">
          <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
            {c.label}
          </div>
          <div className="mono text-lg">
            {c.value}
            {c.suffix ? <span className="text-xs ml-1 text-[color:var(--fg-muted)]">{c.suffix}</span> : null}
          </div>
          {typeof c.delta === "number" ? (
            <div
              className={[
                "text-xs mono",
                c.delta > 0 ? "text-[color:var(--pos)]" : c.delta < 0 ? "text-[color:var(--neg)]" : "text-[color:var(--neutral)]",
              ].join(" ")}
            >
              {c.delta > 0 ? "+" : ""}
              {c.delta}
            </div>
          ) : null}
        </div>
      ))}
    </Tag>
  );
}
