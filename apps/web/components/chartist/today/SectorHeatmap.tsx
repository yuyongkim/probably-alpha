// SectorHeatmap — 20+ sectors × 5 periods; color buckets h0..h6.
// Ported from mockup `.heatmap` grid. Read-only display, no click handlers yet.
import type { SectorHeatRow } from "@/types/chartist";

interface Props {
  rows: SectorHeatRow[];
}

function signed(v: number): string {
  return v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2);
}

function Cell({ value, bucket }: { value: number; bucket: number }) {
  return <div className={`hm-cell h${bucket}`}>{signed(value)}</div>;
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
          {rows.length} SECTORS · 1D / 1W / 1M / 3M / YTD
        </span>
      </div>
      <div className="p-[10px]">
        <div className="hm-grid">
          <div className="hm-head first">Sector</div>
          <div className="hm-head">1D</div>
          <div className="hm-head">1W</div>
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

// Grid is a flat list of cells (no implicit rows in CSS grid); a helper
// component keeps the JSX readable without introducing wrapping divs.
function ROW({ r }: { r: SectorHeatRow }) {
  return (
    <>
      <div className="hm-name">{r.name}</div>
      <Cell value={r.p1d} bucket={r.p1d_h} />
      <Cell value={r.p1w} bucket={r.p1w_h} />
      <Cell value={r.p1m} bucket={r.p1m_h} />
      <Cell value={r.p3m} bucket={r.p3m_h} />
      <Cell value={r.pytd} bucket={r.pytd_h} />
    </>
  );
}
