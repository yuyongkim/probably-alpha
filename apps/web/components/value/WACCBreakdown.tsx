// WACC breakdown — capital structure + cost legs.

import type { WaccResponse } from "@/types/value";

const pct = (v: number | null | undefined, digits = 2) =>
  v == null ? "–" : `${(v * 100).toFixed(digits)}%`;

export function WACCBreakdown({ wacc }: { wacc: WaccResponse }) {
  return (
    <section className="space-y-3">
      <header>
        <h3 className="display text-lg">WACC — {wacc.symbol}</h3>
        <p className="text-xs text-[color:var(--fg-muted)]">
          as of {wacc.as_of ?? "latest"} · CAPM · KR 10Y baseline
          {wacc.fallback ? " · 50/50 fallback (missing balance sheet)" : ""}
        </p>
      </header>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-3 border border-border rounded-md bg-[color:var(--surface)]">
        <Stat label="WACC" v={wacc.wacc} strong />
        <Stat label="Cost of Equity" v={wacc.cost_of_equity} />
        <Stat label="Cost of Debt (AT)" v={wacc.cost_of_debt_after_tax} />
        <Stat label="Rf" v={wacc.rf} />
      </div>
      <div className="grid grid-cols-2 gap-4 p-3 border border-border rounded-md bg-[color:var(--surface)]">
        <div>
          <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">Equity Weight</div>
          <div className="mono text-xl">{pct(wacc.w_equity)}</div>
          <div className="h-2 bg-[color:var(--surface-2)] rounded mt-2 overflow-hidden">
            <div className="h-full bg-[color:var(--pos)]" style={{ width: `${(wacc.w_equity ?? 0) * 100}%` }} />
          </div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">Debt Weight</div>
          <div className="mono text-xl">{pct(wacc.w_debt)}</div>
          <div className="h-2 bg-[color:var(--surface-2)] rounded mt-2 overflow-hidden">
            <div className="h-full bg-[color:var(--neg)]" style={{ width: `${(wacc.w_debt ?? 0) * 100}%` }} />
          </div>
        </div>
      </div>
      <p className="text-xs text-[color:var(--fg-muted)]">
        CAPM: cost_of_equity = rf + β × ERP = {pct(wacc.rf)} + {wacc.beta} × {pct(wacc.erp)} = {pct(wacc.cost_of_equity)}
      </p>
    </section>
  );
}

function Stat({ label, v, strong = false }: { label: string; v: number | null | undefined; strong?: boolean }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">{label}</div>
      <div className={`mono ${strong ? "text-2xl text-[color:var(--accent)]" : "text-lg"}`}>{pct(v)}</div>
    </div>
  );
}
