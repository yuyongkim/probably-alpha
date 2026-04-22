// DCF result card — intrinsic value vs market, stage-1 cash flows.

import type { DcfResponse } from "@/types/value";

const fmt = (v: number | null | undefined, digits = 0) =>
  v == null ? "–" : v.toLocaleString(undefined, { maximumFractionDigits: digits });

export function DCFResult({ dcf }: { dcf: DcfResponse }) {
  const per = dcf.per_share_value;
  return (
    <section className="space-y-4">
      <header>
        <h3 className="display text-lg">DCF — {dcf.symbol}</h3>
        <p className="text-xs text-[color:var(--fg-muted)]">
          as of {dcf.as_of} · growth_high={(dcf.assumptions.growth_high * 100).toFixed(1)}% ·
          term={(dcf.assumptions.growth_term * 100).toFixed(1)}% · wacc={(dcf.assumptions.wacc * 100).toFixed(2)}%
        </p>
      </header>
      <div className="grid grid-cols-4 gap-4 p-3 border border-border rounded-md bg-[color:var(--surface)]">
        <Stat label="FCF0" v={dcf.fcf0} suffix="KRW" />
        <Stat label="PV Stage1" v={dcf.pv_stage1} suffix="KRW" />
        <Stat label="PV Terminal" v={dcf.pv_terminal} suffix="KRW" />
        <Stat label="Enterprise" v={dcf.enterprise_value} suffix="KRW" />
      </div>
      <div className="grid grid-cols-2 gap-4 p-3 border border-border rounded-md bg-[color:var(--surface)]">
        <Stat label="Per-Share (proxy)" v={per} suffix="KRW" tone={per != null && per > 0 ? "pos" : "neg"} />
        <Stat label="Shares proxy" v={dcf.shares_outstanding_proxy} suffix="shares" />
      </div>
      <div className="border border-border rounded-md overflow-x-auto">
        <table className="w-full text-sm mono">
          <thead className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
            <tr>
              <th className="px-2 py-1 text-right">Year</th>
              <th className="px-2 py-1 text-right">Projected FCF</th>
              <th className="px-2 py-1 text-right">PV</th>
            </tr>
          </thead>
          <tbody>
            {dcf.stage1.map((s) => (
              <tr key={s.year} className="border-b border-[color:var(--border-soft)]">
                <td className="px-2 py-1 text-right">t+{s.year}</td>
                <td className="px-2 py-1 text-right">{fmt(s.fcf)}</td>
                <td className="px-2 py-1 text-right">{fmt(s.pv)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-[color:var(--fg-muted)]">
        per_share is approximate — shares outstanding inferred from PIT equity × 1.5 / close.
        Override with real shares for production-grade valuation.
      </p>
    </section>
  );
}

function Stat({ label, v, suffix, tone }: { label: string; v: number | null | undefined; suffix: string; tone?: "pos" | "neg" }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">{label}</div>
      <div className={`mono text-lg ${tone === "pos" ? "text-[color:var(--pos)]" : tone === "neg" ? "text-[color:var(--neg)]" : ""}`}>
        {fmt(v)}
      </div>
      <div className="text-xs text-[color:var(--fg-muted)]">{suffix}</div>
    </div>
  );
}
