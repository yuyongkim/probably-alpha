// Altman Z-Score gauge — shows zone + component breakdown.

import type { AltmanResponse } from "@/types/value";

const ZONE_COLOR: Record<string, string> = {
  safe: "var(--pos)",
  grey: "var(--neutral)",
  distress: "var(--neg)",
};

export function AltmanGauge({ z }: { z: AltmanResponse }) {
  const pct = Math.min(Math.max(z.z_score / 6, 0), 1);
  return (
    <section className="space-y-3">
      <header>
        <h3 className="display text-lg">Altman Z-Score — {z.symbol}</h3>
        <p className="text-xs text-[color:var(--fg-muted)]">
          as of {z.as_of} · {z.proxy ? "proxy balance-sheet fields used" : "full inputs"}
        </p>
      </header>
      <div className="p-3 border border-border rounded-md bg-[color:var(--surface)]">
        <div className="flex items-baseline justify-between mb-2">
          <span className="mono text-3xl">{z.z_score.toFixed(2)}</span>
          <span
            className="uppercase tracking-widest text-xs px-2 py-1 rounded"
            style={{ background: ZONE_COLOR[z.zone], color: "var(--surface)" }}
          >
            {z.zone}
          </span>
        </div>
        <div className="h-2 bg-[color:var(--surface-2)] rounded overflow-hidden">
          <div className="h-full" style={{ width: `${pct * 100}%`, background: ZONE_COLOR[z.zone] }} />
        </div>
        <div className="flex justify-between text-xs mt-1 text-[color:var(--fg-muted)]">
          <span>distress &lt; 1.81</span>
          <span>grey 1.81 – 2.99</span>
          <span>safe &gt; 2.99</span>
        </div>
      </div>
      <div className="grid grid-cols-5 gap-2">
        <Component label="A = WC/TA" v={z.A_wc_assets} weight={1.2} />
        <Component label="B = RE/TA" v={z.B_re_assets} weight={1.4} />
        <Component label="C = EBIT/TA" v={z.C_ebit_assets} weight={3.3} />
        <Component label="D = MC/TL" v={z.D_mcap_liab} weight={0.6} />
        <Component label="E = Sales/TA" v={z.E_sales_assets} weight={1.0} />
      </div>
    </section>
  );
}

function Component({ label, v, weight }: { label: string; v: number; weight: number }) {
  return (
    <div className="p-2 border border-border rounded bg-[color:var(--surface)]">
      <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">{label}</div>
      <div className="mono text-sm">{v.toFixed(3)}</div>
      <div className="text-[10px] text-[color:var(--fg-muted)]">× {weight}</div>
    </div>
  );
}
