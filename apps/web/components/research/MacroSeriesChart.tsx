// MacroSeriesChart — tiny SVG line chart for one macro series.
import type { MacroSeriesResponse } from "@/types/macro";

interface Props {
  label: string;
  data: MacroSeriesResponse;
}

export function MacroSeriesChart({ label, data }: Props) {
  const values = data.observations
    .map((o) => o.value)
    .filter((v): v is number => v !== null);
  if (values.length < 2) {
    return (
      <div
        className="rounded-md border p-3 text-xs text-[color:var(--fg-muted)]"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div className="display text-sm mb-1">{label}</div>
        {data.warning ?? "not enough data"}
      </div>
    );
  }
  const W = 640;
  const H = 140;
  const PAD = 14;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, 1e-6);
  const step = (W - PAD * 2) / (values.length - 1);
  const path = values
    .map((v, i) => {
      const x = PAD + i * step;
      const y = PAD + (H - PAD * 2) - ((v - min) / span) * (H - PAD * 2);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const last = values[values.length - 1];
  const first = values[0];
  const change = last - first;
  const pct = (change / first) * 100;
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="flex items-baseline justify-between px-3 py-2 border-b"
           style={{ borderColor: "var(--border)" }}>
        <div>
          <div className="display text-sm">{label}</div>
          <div className="text-[11px] mono text-[color:var(--fg-muted)]">
            {data.source}:{data.series_id} · {values.length} obs
          </div>
        </div>
        <div className="mono text-sm" style={{ color: pct >= 0 ? "var(--pos)" : "var(--neg)" }}>
          {last.toFixed(2)} ({pct >= 0 ? "+" : ""}{pct.toFixed(1)}%)
        </div>
      </div>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} className="w-full block"
           style={{ background: "var(--surface-2)" }}>
        <path d={path} fill="none" stroke="var(--accent)" strokeWidth={1.5} />
      </svg>
    </div>
  );
}
