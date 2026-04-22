// WizardPage — reusable page template for /chartist/wizards/[name].
// Renders a rules-card header + dense pass list.
import type { WizardDetail } from "@/types/chartist";
import type { WizardConfig } from "@/lib/wizards";
import { TickerName } from "@/components/shared/TickerName";

interface Props {
  detail: WizardDetail;
  config: WizardConfig;
}

const TH =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b";
const NUM = "py-1 px-2 mono text-[11px] text-right tabular-nums";

function signed(v: number, digits = 2): string {
  return v > 0 ? `+${v.toFixed(digits)}` : v.toFixed(digits);
}

function tone(v: number): string {
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

export function WizardPage({ detail, config }: Props) {
  return (
    <div className="flex flex-col gap-3">
      <div>
        <h1 className="display text-3xl">{config.name}</h1>
        <div className="text-xs text-[color:var(--fg-muted)] mt-1">
          {detail.as_of} CLOSE · {detail.count}개 통과 · {detail.condition}
        </div>
      </div>

      <blockquote
        className="px-4 py-3 text-[12.5px] italic border-l-2 text-[color:var(--fg-muted)]"
        style={{ borderColor: "var(--accent)", background: "var(--surface-2)" }}
      >
        "{config.quote}"
      </blockquote>

      <div
        className="rounded-md border p-4"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)] mb-2">
          Rules
        </div>
        <ol className="list-decimal pl-5 flex flex-col gap-1 text-[12px]">
          {config.rules.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ol>
      </div>

      <div
        className="rounded-md border overflow-hidden"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div
          className="flex items-baseline justify-between px-3 py-2 border-b"
          style={{ borderColor: "var(--border)" }}
        >
          <h2 className="display text-base">Pass List</h2>
          <span className="text-[10px] text-[color:var(--fg-muted)]">
            {detail.rows.length} 종목
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[11.5px] border-collapse">
            <thead>
              <tr>
                <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>#</th>
                <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>Ticker</th>
                <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>Market</th>
                <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>Sector</th>
                <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>Close</th>
                <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>1D</th>
                <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>Vol×</th>
                <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>왜 통과?</th>
              </tr>
            </thead>
            <tbody>
              {detail.rows.map((h, i) => (
                <tr
                  key={h.symbol}
                  style={{ borderBottom: "1px solid var(--border-soft)" }}
                  className="hover:bg-[color:var(--surface-2)]"
                >
                  <td className="py-1 px-2 mono text-[10px] text-[color:var(--fg-muted)]">{i + 1}</td>
                  <td className="py-1 px-2">
                    <TickerName symbol={h.symbol} name={h.name} sector={h.sector} />
                    <span className="mono ml-2 text-[10px] text-[color:var(--fg-muted)]">{h.symbol}</span>
                  </td>
                  <td className="py-1 px-2 text-[10.5px] text-[color:var(--fg-muted)]">{h.market}</td>
                  <td className="py-1 px-2 text-[10.5px]">{h.sector}</td>
                  <td className={NUM}>{h.close.toLocaleString()}</td>
                  <td className={NUM} style={{ color: tone(h.pct_1d) }}>{signed(h.pct_1d)}</td>
                  <td className={NUM}>{h.vol_x.toFixed(1)}×</td>
                  <td className="py-1 px-2 text-[10.5px] text-[color:var(--fg-muted)]">{h.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
