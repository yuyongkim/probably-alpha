// Financial Trend — 8Q revenue / op income / net income table.

import type { TrendResponse, TrendRow } from "@/types/value";

const fmt = (v: number | null, digits = 0) =>
  v == null ? "–" : v.toLocaleString(undefined, { maximumFractionDigits: digits });

export function FinancialTrend({ trend }: { trend: TrendResponse }) {
  return (
    <section className="space-y-3">
      <header>
        <h3 className="display text-lg">
          재무 트렌드 — {trend.meta?.name || trend.symbol}
        </h3>
        <p className="text-xs text-[color:var(--fg-muted)]">
          {trend.symbol} · {trend.meta?.sector || "—"} · ky.db financials_pit
        </p>
      </header>
      <div className="border border-border rounded-md overflow-x-auto">
        <table className="w-full text-sm mono">
          <thead className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
            <tr>
              <th className="px-2 py-1 text-left">Period</th>
              <th className="px-2 py-1 text-left">Type</th>
              <th className="px-2 py-1 text-right">Revenue</th>
              <th className="px-2 py-1 text-right">OpInc</th>
              <th className="px-2 py-1 text-right">NetInc</th>
              <th className="px-2 py-1 text-right">OpMargin%</th>
              <th className="px-2 py-1 text-left">Source</th>
            </tr>
          </thead>
          <tbody>
            {trend.series.map((r, i) => (
              <Row key={`${r.period_end}-${r.period_type}-${i}`} r={r} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Row({ r }: { r: TrendRow }) {
  const om =
    r.revenue && r.operating_income != null && r.revenue > 0
      ? (r.operating_income / r.revenue) * 100
      : null;
  return (
    <tr className="border-b border-[color:var(--border-soft)]">
      <td className="px-2 py-1">{r.period_end}</td>
      <td className="px-2 py-1">{r.period_type}</td>
      <td className="px-2 py-1 text-right">{fmt(r.revenue)}</td>
      <td className="px-2 py-1 text-right">{fmt(r.operating_income)}</td>
      <td className="px-2 py-1 text-right">{fmt(r.net_income)}</td>
      <td className="px-2 py-1 text-right">{om == null ? "–" : om.toFixed(1)}</td>
      <td className="px-2 py-1 text-xs text-[color:var(--fg-muted)]">{r.source_id}</td>
    </tr>
  );
}
