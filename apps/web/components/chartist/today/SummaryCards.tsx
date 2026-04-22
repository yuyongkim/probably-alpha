// SummaryCards — 6 KPI cards modeled on mockup `.summary-row` + `.summary-card`.
import type { SummaryKPI, Tone } from "@/types/chartist";

interface Props {
  items: SummaryKPI[];
}

function toneClass(tone: Tone): string {
  if (tone === "pos") return "text-[color:var(--pos)]";
  if (tone === "neg") return "text-[color:var(--neg)]";
  return "text-[color:var(--fg-muted)]";
}

export function SummaryCards({ items }: Props) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 mb-3">
      {items.map((c) => (
        <div
          key={c.label}
          className="rounded-md px-3 py-2 border"
          style={{
            background: "var(--surface)",
            borderColor: "var(--border)",
          }}
        >
          <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)] font-medium mb-1">
            {c.label}
          </div>
          <div
            className="display text-[18px] font-medium leading-tight"
            style={{ letterSpacing: "-0.02em" }}
          >
            {c.value}
          </div>
          <div className={`mono text-[10.5px] font-medium mt-0.5 ${toneClass(c.tone)}`}>
            {c.delta}
          </div>
        </div>
      ))}
    </div>
  );
}
