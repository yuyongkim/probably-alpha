// PIT Timeline — stacks financial series by quarter, colour-coded by source.

import type { PITResponse, PITSeriesRow } from "@/types/quant";

const fmt = (v: number | null, digits = 0) =>
  v == null ? "–" : v.toLocaleString(undefined, { maximumFractionDigits: digits });

function unitScaleLabel(src: string): string {
  return src === "quant_platform_pit" ? "KRW" : "억 KRW";
}

export function PITTimeline({ pit }: { pit: PITResponse }) {
  const ttm = pit.ttm;
  return (
    <section className="space-y-4">
      <header>
        <h3 className="display text-lg">{pit.meta?.name || pit.symbol}</h3>
        <p className="text-xs text-[color:var(--fg-muted)]">
          {pit.symbol} · {pit.meta?.sector || "—"} · PIT as of {pit.as_of}
        </p>
      </header>
      {ttm && (
        <div className="grid grid-cols-4 gap-4 p-3 border border-border rounded-md bg-[color:var(--surface)]">
          <Stat label="Revenue TTM" v={ttm.revenue_ttm} suffix="KRW" />
          <Stat label="OpIncome TTM" v={ttm.operating_income_ttm} suffix="KRW" />
          <Stat label="NetIncome TTM" v={ttm.net_income_ttm} suffix="KRW" />
          <Stat label="Total Equity" v={ttm.total_equity} suffix="KRW" />
        </div>
      )}
      <div className="border border-border rounded-md overflow-x-auto">
        <table className="w-full text-sm mono">
          <thead className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
            <tr>
              <th className="px-2 py-1 text-left">Period</th>
              <th className="px-2 py-1 text-left">Type</th>
              <th className="px-2 py-1 text-right">Revenue</th>
              <th className="px-2 py-1 text-right">OpIncome</th>
              <th className="px-2 py-1 text-right">NetIncome</th>
              <th className="px-2 py-1 text-right">TotalAssets</th>
              <th className="px-2 py-1 text-left">Source / Unit</th>
            </tr>
          </thead>
          <tbody>
            {pit.series.map((r, i) => (
              <Row key={`${r.period_end}-${r.period_type}-${i}`} r={r} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Row({ r }: { r: PITSeriesRow }) {
  return (
    <tr className="border-b border-[color:var(--border-soft)]">
      <td className="px-2 py-1">{r.period_end}</td>
      <td className="px-2 py-1">{r.period_type}</td>
      <td className="px-2 py-1 text-right">{fmt(r.revenue)}</td>
      <td className="px-2 py-1 text-right">{fmt(r.operating_income)}</td>
      <td className="px-2 py-1 text-right">{fmt(r.net_income)}</td>
      <td className="px-2 py-1 text-right">{fmt(r.total_assets)}</td>
      <td className="px-2 py-1 text-xs text-[color:var(--fg-muted)]">
        {r.source_id} · {unitScaleLabel(r.source_id)}
      </td>
    </tr>
  );
}

function Stat({ label, v, suffix }: { label: string; v: number | null; suffix: string }) {
  return (
    <div className="min-w-0">
      <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">{label}</div>
      <div className="mono text-lg">{fmt(v)}</div>
      <div className="text-xs text-[color:var(--fg-muted)]">{suffix}</div>
    </div>
  );
}
