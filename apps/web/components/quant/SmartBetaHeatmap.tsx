// Smart Beta allocation — weight bars as a heatmap-style column.

import type { SmartBetaHolding } from "@/types/quant";

export function SmartBetaHeatmap({
  holdings,
  variant,
}: {
  holdings: SmartBetaHolding[];
  variant: string;
}) {
  const maxW = Math.max(...holdings.map((h) => h.weight || 0), 0.0001);
  return (
    <section className="border border-border rounded-md p-4 bg-[color:var(--surface)]">
      <header className="flex items-baseline justify-between mb-3">
        <h3 className="display text-lg capitalize">
          {variant.replace("_", " ")} Smart Beta
        </h3>
        <span className="text-xs text-[color:var(--fg-muted)]">
          {holdings.length} holdings
        </span>
      </header>
      <ul className="space-y-1">
        {holdings.map((h) => (
          <li key={h.symbol} className="grid grid-cols-[80px_1fr_auto] gap-3 items-center text-sm mono">
            <span>{h.symbol}</span>
            <span className="truncate" title={h.name || ""}>{h.name || "—"}</span>
            <span className="flex items-center gap-2">
              <span className="inline-block h-2 bg-[color:var(--accent)] rounded" style={{ width: `${(h.weight / maxW) * 140}px` }} />
              <span className="text-xs">{(h.weight * 100).toFixed(2)}%</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
