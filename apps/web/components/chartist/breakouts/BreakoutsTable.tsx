// BreakoutsTable — 52-week breakouts with volume confirmation.
import type { BreakoutRow52w } from "@/types/chartist";
import { TickerName } from "@/components/shared/TickerName";

interface Props {
  rows: BreakoutRow52w[];
}

const TH =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b";
const NUM = "py-1 px-2 mono text-[11px] text-right tabular-nums";

export function BreakoutsTable({ rows }: Props) {
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">52-Week Breakouts</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          {rows.length} 종목 · close ≥ 52w high · vol ≥ 1.5×
        </span>
      </div>
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              Ticker
            </th>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              Market
            </th>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              Sector
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              Close
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              52w High
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              %↑ (1D)
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              Vol×
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((b) => (
            <tr
              key={b.symbol}
              style={{ borderBottom: "1px solid var(--border-soft)" }}
              className="hover:bg-[color:var(--surface-2)]"
            >
              <td className="py-1 px-2">
                <TickerName symbol={b.symbol} name={b.name} sector={b.sector} />
                <span className="mono ml-2 text-[10px] text-[color:var(--fg-muted)]">
                  {b.symbol}
                </span>
              </td>
              <td className="py-1 px-2 text-[10.5px] text-[color:var(--fg-muted)]">{b.market}</td>
              <td className="py-1 px-2 text-[10.5px]">{b.sector}</td>
              <td className={NUM}>{b.close.toLocaleString()}</td>
              <td className={NUM}>{b.high52w.toLocaleString()}</td>
              <td className={NUM} style={{ color: "var(--pos)" }}>
                +{b.pct_up.toFixed(2)}
              </td>
              <td className={NUM}>{b.vol_x.toFixed(1)}×</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
