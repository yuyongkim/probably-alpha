// TopSectorsList — 5-row sector ranking with a mini sparkline SVG.
import type { Sector } from "@/types/chartist";

interface Props {
  sectors: Sector[];
}

function signed(v: number): string {
  return v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2);
}

function toneStyle(v: number): string {
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

function Sparkline({ points }: { points: number[] }) {
  if (points.length < 2) return null;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = Math.max(max - min, 1e-6);
  const W = 64;
  const H = 20;
  const step = W / (points.length - 1);
  const path = points
    .map((p, i) => {
      const x = i * step;
      const y = H - ((p - min) / span) * H;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={W} height={H} aria-hidden>
      <path d={path} fill="none" stroke="var(--accent)" strokeWidth={1.25} />
    </svg>
  );
}

export function TopSectorsList({ sectors }: Props) {
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
      }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">Top Sectors</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">Strength · 7D spark</span>
      </div>
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
            <th className="py-1.5 px-2 text-left font-medium">#</th>
            <th className="py-1.5 px-2 text-left font-medium">Sector</th>
            <th className="py-1.5 px-2 text-right font-medium">Sc</th>
            <th className="py-1.5 px-2 text-right font-medium">1D</th>
            <th className="py-1.5 px-2 text-right font-medium">5D</th>
            <th className="py-1.5 px-2 text-right font-medium">Trend</th>
          </tr>
        </thead>
        <tbody>
          {sectors.map((s) => (
            <tr
              key={s.rank}
              style={{ borderTop: "1px solid var(--border-soft)" }}
              className="hover:bg-[color:var(--surface-2)]"
            >
              <td className="py-1 px-2 mono text-[10.5px] text-[color:var(--fg-muted)]">
                {String(s.rank).padStart(2, "0")}
              </td>
              <td className="py-1 px-2 font-medium">{s.name}</td>
              <td className="py-1 px-2 mono text-[11px] text-right tabular-nums">
                {s.score.toFixed(2)}
              </td>
              <td
                className="py-1 px-2 mono text-[11px] text-right tabular-nums"
                style={{ color: toneStyle(s.d1) }}
              >
                {signed(s.d1)}
              </td>
              <td
                className="py-1 px-2 mono text-[11px] text-right tabular-nums"
                style={{ color: toneStyle(s.d5) }}
              >
                {signed(s.d5)}
              </td>
              <td className="py-1 px-2">
                <div className="flex justify-end">
                  <Sparkline points={s.sparkline} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
