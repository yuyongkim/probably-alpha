// Piotroski F-Score — 9 binary flags with colour-coded chips.

import type { PiotroskiResponse } from "@/types/value";

const LABELS: Record<string, string> = {
  roa_positive: "ROA > 0",
  cfo_positive: "CFO > 0 (n/a)",
  delta_roa: "ΔROA > 0",
  accrual: "CFO > NI (n/a)",
  delta_leverage: "Δ부채비율 ↓",
  delta_liquidity: "Δ유동성 (n/a)",
  no_new_shares: "주식수 ≤ (n/a)",
  delta_margin: "Δ영업이익률 ↑",
  delta_turnover: "Δ자산회전율 ↑",
};

export function PiotroskiBreakdown({ p }: { p: PiotroskiResponse }) {
  return (
    <section className="space-y-3">
      <header>
        <h3 className="display text-lg">Piotroski F-Score — {p.symbol}</h3>
        <p className="text-xs text-[color:var(--fg-muted)]">
          as of {p.as_of} · {p.score}/{p.max_possible} flags (n/a 제외)
        </p>
      </header>
      <div className="grid grid-cols-3 gap-2">
        {Object.entries(p.flags).map(([k, v]) => (
          <div
            key={k}
            className={[
              "p-2 rounded-md border text-sm",
              v === 1
                ? "border-[color:var(--pos)] bg-[color:var(--surface)]"
                : v === 0
                ? "border-[color:var(--neg)] bg-[color:var(--surface)]"
                : "border-dashed border-border text-[color:var(--fg-muted)]",
            ].join(" ")}
          >
            <div className="text-[10px] uppercase tracking-widest">{LABELS[k] ?? k}</div>
            <div className="mono">
              {v === 1 ? "PASS" : v === 0 ? "FAIL" : "n/a"}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
