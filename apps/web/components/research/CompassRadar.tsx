// CompassRadar — 4-axis radar chart (growth / inflation / liquidity / credit).
// Rendered server-side; SVG only. Target ≤ 120 lines.
import type { CompassResponse } from "@/types/macro";

interface Props {
  compass: CompassResponse;
}

const AXES: Array<[keyof CompassResponse["axes"], string]> = [
  ["growth", "성장"],
  ["inflation", "물가"],
  ["liquidity", "유동성"],
  ["credit", "신용"],
];

export function CompassRadar({ compass }: Props) {
  const size = 280;
  const cx = size / 2;
  const cy = size / 2;
  const R = 100;

  // Map score [-1..1] to radius [20%..100% of R].
  const rOf = (score: number) => {
    const normalized = (score + 1) / 2; // [0..1]
    return 20 + normalized * (R - 20);
  };

  const points = AXES.map(([id], i) => {
    const theta = (i / AXES.length) * Math.PI * 2 - Math.PI / 2;
    const r = rOf(compass.axes[id].score);
    return {
      x: cx + Math.cos(theta) * r,
      y: cy + Math.sin(theta) * r,
      label: AXES[i][1],
      labelX: cx + Math.cos(theta) * (R + 14),
      labelY: cy + Math.sin(theta) * (R + 14),
      score: compass.axes[id].score,
    };
  });

  const path = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ") + " Z";

  return (
    <div
      className="rounded-md border p-3"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="flex items-baseline justify-between mb-2">
        <h3 className="display text-base">Macro Compass</h3>
        <span
          className="mono text-sm"
          style={{ color: compass.composite >= 0 ? "var(--pos)" : "var(--neg)" }}
        >
          {compass.regime_hint} · {compass.composite.toFixed(2)}
        </span>
      </div>
      <svg width={size} height={size} className="block mx-auto" aria-hidden>
        {/* concentric rings */}
        {[0.25, 0.5, 0.75, 1.0].map((f) => (
          <circle
            key={f}
            cx={cx}
            cy={cy}
            r={R * f}
            fill="none"
            stroke="var(--border-soft)"
            strokeWidth={0.5}
          />
        ))}
        {/* axes */}
        {points.map((p, i) => {
          const theta = (i / AXES.length) * Math.PI * 2 - Math.PI / 2;
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={cx + Math.cos(theta) * R}
              y2={cy + Math.sin(theta) * R}
              stroke="var(--border-soft)"
              strokeWidth={0.5}
            />
          );
        })}
        {/* plot */}
        <path d={path} fill="rgba(27,95,72,0.22)" stroke="var(--accent)" strokeWidth={1.25} />
        {points.map((p) => (
          <circle key={p.label} cx={p.x} cy={p.y} r={3} fill="var(--accent)" />
        ))}
        {/* labels */}
        {points.map((p) => (
          <text
            key={p.label}
            x={p.labelX}
            y={p.labelY}
            textAnchor="middle"
            className="mono"
            style={{ fontSize: 11, fill: "var(--fg-muted)" }}
          >
            {p.label} {p.score.toFixed(2)}
          </text>
        ))}
      </svg>
      {compass.stale ? (
        <div className="text-[11px] mt-2" style={{ color: "var(--neg)" }}>
          Stale: {compass.warnings.join(", ")}
        </div>
      ) : null}
    </div>
  );
}
