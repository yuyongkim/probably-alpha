// WizardsOverview — 6 cards summarising preset pass counts.
import type { WizardsOverview } from "@/types/chartist";
import Link from "next/link";

interface Props {
  data: WizardsOverview;
}

function pctStr(n: number, total: number): string {
  if (!total) return "—";
  return `${((n / total) * 100).toFixed(2)}%`;
}

function deltaStyle(d: number): string {
  if (d > 0) return "var(--pos)";
  if (d < 0) return "var(--neg)";
  return "var(--neutral)";
}

export function WizardsOverview({ data }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {data.presets.map((p) => (
        <Link
          key={p.key}
          href={`/chartist/wizards/${p.key}`}
          className="rounded-md border p-4 flex flex-col gap-2 hover:border-[color:var(--accent)] transition-colors"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          <div className="flex items-baseline justify-between">
            <h3 className="display text-xl">{p.name}</h3>
            <span className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
              {p.key}
            </span>
          </div>
          <div className="text-[11px] text-[color:var(--fg-muted)]">{p.condition}</div>
          <div className="mt-2 flex items-baseline gap-3">
            <span
              className="display text-[32px] font-medium"
              style={{ letterSpacing: "-0.02em" }}
            >
              {p.pass_count}
            </span>
            <span className="mono text-[11px] text-[color:var(--fg-muted)]">
              / {p.total.toLocaleString()} · {pctStr(p.pass_count, p.total)}
            </span>
          </div>
          <div
            className="mono text-[11px]"
            style={{ color: deltaStyle(p.delta_vs_yesterday) }}
          >
            Δ 어제 {p.delta_vs_yesterday > 0 ? "+" : ""}{p.delta_vs_yesterday}
          </div>
        </Link>
      ))}
    </div>
  );
}
