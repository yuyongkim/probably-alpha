// IC / hit-rate bar for a single factor.

import type { ICResponse } from "@/types/quant";

export function ICBar({ ic }: { ic: ICResponse }) {
  const icVal = ic.ic ?? 0;
  const width = Math.min(Math.abs(icVal) * 400, 200);
  const tone = icVal > 0 ? "pos" : icVal < 0 ? "neg" : "neutral";
  return (
    <section className="border border-border rounded-md p-4 bg-[color:var(--surface)] space-y-2">
      <div className="flex justify-between items-baseline">
        <h3 className="display text-lg capitalize">{ic.factor} IC</h3>
        <span className="text-xs text-[color:var(--fg-muted)]">
          {ic.period} · as of {ic.as_of} · n={ic.n}
        </span>
      </div>
      <div className="flex items-center gap-4">
        <span
          className="h-2 rounded"
          style={{
            width: `${width}px`,
            background:
              tone === "pos"
                ? "var(--pos)"
                : tone === "neg"
                ? "var(--neg)"
                : "var(--neutral)",
          }}
        />
        <span className={`mono text-xl ${tone === "pos" ? "text-[color:var(--pos)]" : tone === "neg" ? "text-[color:var(--neg)]" : ""}`}>
          {icVal.toFixed(3)}
        </span>
      </div>
      <div className="text-sm">
        Hit rate: <span className="mono">{(ic.hit_rate * 100).toFixed(1)}%</span>
      </div>
    </section>
  );
}
