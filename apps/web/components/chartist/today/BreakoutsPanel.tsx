// BreakoutsPanel — 10 symbols that printed a 52-week high today.
// Sits in the 4-panel grid alongside Top Leaders / Top Sectors.
import type { Breakout } from "@/types/chartist";
import { TickerName } from "@/components/shared/TickerName";

interface Props {
  items: Breakout[];
}

const TH =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b";
const TD_NUM = "py-1 px-2 mono text-[11px] text-right tabular-nums";

export function BreakoutsPanel({ items }: Props) {
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">52w 돌파</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">오늘</span>
      </div>
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              Ticker
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              %↑
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              Vol×
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((b) => (
            <tr
              key={b.symbol}
              style={{ borderBottom: "1px solid var(--border-soft)" }}
              className="hover:bg-[color:var(--surface-2)]"
            >
              <td className="py-1 px-2">
                <TickerName symbol={b.symbol} name={b.ticker} sector={b.sector} />
              </td>
              <td className={TD_NUM} style={{ color: "var(--pos)" }}>
                +{b.pct_up.toFixed(2)}
              </td>
              <td className={TD_NUM}>{b.vol_x.toFixed(1)}×</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
