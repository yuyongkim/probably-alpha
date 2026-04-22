// SectorHeatmap — full 28-row heatmap with color buckets.
// Ports the `hm-*` classes from globals.css. Same component as
// the "Today" page heatmap, just rendered on its own page with
// full member count column.
import type { SectorRow } from "@/types/chartist";

interface Props {
  rows: SectorRow[];
}

function signed(v: number): string {
  return v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2);
}

function bucket(pct: number): number {
  if (pct <= -3) return 1;
  if (pct <= -1) return 2;
  if (pct < 0) return 3;
  if (pct < 1) return 4;
  if (pct < 3) return 5;
  return 6;
}

function Cell({ value }: { value: number }) {
  const b = bucket(value);
  return <div className={`hm-cell h${b}`}>{signed(value)}</div>;
}

export function SectorHeatmap({ rows }: Props) {
  return (
    <div
      className="rounded-md border overflow-hidden mb-3"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">Sector Heatmap</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          {rows.length} SECTORS · 1D / 5D / 1M / 3M / YTD
        </span>
      </div>
      <div className="p-[10px]">
        <div
          className="hm-grid"
          style={{ gridTemplateColumns: "170px 56px repeat(5, 1fr)" }}
        >
          <div className="hm-head first">Sector</div>
          <div className="hm-head">N</div>
          <div className="hm-head">1D</div>
          <div className="hm-head">5D</div>
          <div className="hm-head">1M</div>
          <div className="hm-head">3M</div>
          <div className="hm-head">YTD</div>
          {rows.map((r) => (
            <ROW key={r.name} r={r} />
          ))}
        </div>
      </div>
    </div>
  );
}

function ROW({ r }: { r: SectorRow }) {
  return (
    <>
      <div className="hm-name">
        <span className="text-[10.5px] text-[color:var(--muted)] mr-1.5">
          #{String(r.rank).padStart(2, "0")}
        </span>
        {r.name}
      </div>
      <div className="hm-cell" style={{ background: "var(--bg)" }}>
        {r.members}
      </div>
      <Cell value={r.d1 * 100} />
      <Cell value={r.d5 * 100} />
      <Cell value={r.m1 * 100} />
      <Cell value={r.m3 * 100} />
      <Cell value={r.ytd * 100} />
    </>
  );
}
