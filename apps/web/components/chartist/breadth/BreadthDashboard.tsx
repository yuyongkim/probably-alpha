// BreadthDashboard — key breadth metrics tile layout + A/D sparkline.
import type { BreadthResponse } from "@/types/chartist";

interface Props {
  data: BreadthResponse;
}

function fmt(n: number | string, digits = 0): string {
  if (typeof n === "number") return n.toLocaleString(undefined, { maximumFractionDigits: digits });
  return n;
}

function pct(n: number): string {
  return `${n.toFixed(1)}%`;
}

function Tile({
  label,
  value,
  sub,
  tone,
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "pos" | "neg" | "neutral";
}) {
  const color =
    tone === "pos" ? "var(--pos)" : tone === "neg" ? "var(--neg)" : "var(--fg)";
  return (
    <div
      className="rounded-md px-3 py-3 border flex flex-col gap-0.5"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)] font-medium">
        {label}
      </div>
      <div
        className="display text-[22px] font-medium leading-tight"
        style={{ color, letterSpacing: "-0.02em" }}
      >
        {value}
      </div>
      {sub ? (
        <div className="mono text-[10.5px] text-[color:var(--fg-muted)]">{sub}</div>
      ) : null}
    </div>
  );
}

function Sparkline({ points, w = 560, h = 60 }: { points: number[]; w?: number; h?: number }) {
  if (points.length < 2) return null;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = Math.max(max - min, 1);
  const step = w / (points.length - 1);
  const path = points
    .map((p, i) => {
      const x = i * step;
      const y = h - ((p - min) / span) * h;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <path d={path} fill="none" stroke="var(--accent)" strokeWidth={1.5} />
    </svg>
  );
}

export function BreadthDashboard({ data }: Props) {
  const adDiff = data.advancers - data.decliners;
  const adTone: "pos" | "neg" = adDiff >= 0 ? "pos" : "neg";
  const mcTone: "pos" | "neg" = data.mcclellan >= 0 ? "pos" : "neg";

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
        <Tile label="Universe" value={fmt(data.universe)} sub="KOSPI + KOSDAQ" />
        <Tile label="Advancers" value={fmt(data.advancers)} sub={`Dec ${fmt(data.decliners)}`} tone="pos" />
        <Tile label="A/D Diff" value={`${adDiff > 0 ? "+" : ""}${fmt(adDiff)}`} sub={`Unchanged ${fmt(data.unchanged)}`} tone={adTone} />
        <Tile label="% > SMA20" value={pct(data.pct_above_sma20)} sub="short trend" />
        <Tile label="% > SMA50" value={pct(data.pct_above_sma50)} sub="mid trend" />
        <Tile label="% > SMA200" value={pct(data.pct_above_sma200)} sub="long trend" />
        <Tile label="New 52w H" value={fmt(data.new_highs_52w)} sub={`Lows ${fmt(data.new_lows_52w)}`} tone="pos" />
        <Tile label="Up-Vol %" value={pct(data.up_vol_pct)} sub={`total ${fmt(data.up_volume + data.down_volume)}`} tone={data.up_vol_pct >= 50 ? "pos" : "neg"} />
        <Tile
          label="McClellan"
          value={`${data.mcclellan >= 0 ? "+" : ""}${data.mcclellan.toFixed(1)}`}
          sub="EMA19 − EMA39"
          tone={mcTone}
        />
      </div>

      <div
        className="rounded-md border overflow-hidden"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div
          className="flex items-baseline justify-between px-3 py-2 border-b"
          style={{ borderColor: "var(--border)" }}
        >
          <h2 className="display text-base">A/D Line (cumulative)</h2>
          <span className="text-[10px] text-[color:var(--fg-muted)]">
            last {data.ad_line_series.length} trading days
          </span>
        </div>
        <div className="px-3 py-4">
          <Sparkline points={data.ad_line_series} />
        </div>
      </div>
    </div>
  );
}
