// FactorChart — SVG line chart of a factor's cumulative return + stats card.
import type { FactorResult } from "@/types/research";

interface Props {
  result: FactorResult;
}

export function FactorChart({ result }: Props) {
  const n = result.cumulative.length;
  if (n < 5) {
    return (
      <div className="text-xs text-[color:var(--fg-muted)]">
        Not enough data ({n} days). {result.note}
      </div>
    );
  }
  const W = 640;
  const H = 180;
  const PAD = 20;
  const min = Math.min(...result.cumulative, 0);
  const max = Math.max(...result.cumulative, 0);
  const span = Math.max(max - min, 1e-6);
  const step = (W - PAD * 2) / (n - 1);
  const path = result.cumulative
    .map((v, i) => {
      const x = PAD + i * step;
      const y = PAD + (H - PAD * 2) - ((v - min) / span) * (H - PAD * 2);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const last = result.cumulative[n - 1];
  const lastColor = last >= 0 ? "var(--pos)" : "var(--neg)";

  return (
    <div className="rounded-md border overflow-hidden"
         style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
      <div className="flex items-baseline justify-between px-3 py-2 border-b"
           style={{ borderColor: "var(--border)" }}>
        <div>
          <h3 className="display text-base">
            {result.factor}{" "}
            <span className="text-[11px] text-[color:var(--fg-muted)]">
              {result.dates[0]} → {result.dates[n - 1]}
            </span>
          </h3>
          {result.note ? (
            <div className="text-[11px] text-[color:var(--fg-muted)]">{result.note}</div>
          ) : null}
        </div>
        <div className="mono text-sm" style={{ color: lastColor }}>
          {(last * 100).toFixed(2)}%
        </div>
      </div>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="w-full block"
           style={{ background: "var(--surface-2)" }}>
        <line
          x1={PAD} x2={W - PAD}
          y1={PAD + (H - PAD * 2) * (max / span)}
          y2={PAD + (H - PAD * 2) * (max / span)}
          stroke="var(--border)" strokeDasharray="2 4" strokeWidth={0.5}
        />
        <path d={path} fill="none" stroke="var(--accent)" strokeWidth={1.5} />
      </svg>
      <div className="grid grid-cols-5 gap-0 text-[11px] mono border-t"
           style={{ borderColor: "var(--border)" }}>
        {[
          ["Annualised mean", `${(result.stats.mean * 100).toFixed(2)}%`],
          ["Std (ann.)", `${(result.stats.std * 100).toFixed(2)}%`],
          ["Sharpe", result.stats.sharpe.toFixed(2)],
          ["Total", `${(result.stats.total * 100).toFixed(2)}%`],
          ["Universe", result.universe_size.toLocaleString()],
        ].map(([k, v]) => (
          <div key={k} className="py-2 px-3 border-r"
               style={{ borderColor: "var(--border-soft)" }}>
            <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
              {k}
            </div>
            <div className="mono">{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
