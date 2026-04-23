// TradesTable — sortable, dense trade log.
"use client";

import { useMemo, useState } from "react";
import type { BacktestTrade } from "@/types/chartist";

interface Props {
  trades: BacktestTrade[];
  limit?: number;
}

type SortKey =
  | "entry_date"
  | "exit_date"
  | "pnl"
  | "pnl_pct"
  | "holding_days";

const NUM = "py-1 px-2 mono text-[11px] text-right tabular-nums";
const TH =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b select-none cursor-pointer";

function signedPct(v: number, digits = 2): string {
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(digits)}%`;
}

function tone(v: number): string {
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

function exitBadge(reason: string): string {
  switch (reason) {
    case "stop": return "bg-red-500/10 text-[color:var(--neg)] border-[color:var(--neg)]/40";
    case "target": return "bg-green-500/10 text-[color:var(--pos)] border-[color:var(--pos)]/40";
    case "rebalance": return "bg-blue-500/10 text-[color:var(--accent)] border-[color:var(--accent)]/40";
    case "end": return "bg-zinc-500/10 text-[color:var(--fg-muted)] border-[color:var(--border)]";
    default: return "bg-zinc-500/10 text-[color:var(--fg-muted)] border-[color:var(--border)]";
  }
}

export function TradesTable({ trades, limit = 500 }: Props) {
  const [sort, setSort] = useState<SortKey>("exit_date");
  const [desc, setDesc] = useState(true);

  const sorted = useMemo(() => {
    const copy = [...trades];
    copy.sort((a, b) => {
      const va = a[sort];
      const vb = b[sort];
      if (typeof va === "string" && typeof vb === "string") {
        return desc ? vb.localeCompare(va) : va.localeCompare(vb);
      }
      return desc ? (vb as number) - (va as number) : (va as number) - (vb as number);
    });
    return copy.slice(0, limit);
  }, [trades, sort, desc, limit]);

  const click = (key: SortKey) => () => {
    if (sort === key) setDesc((d) => !d);
    else {
      setSort(key);
      setDesc(true);
    }
  };

  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">Trade Log</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          {trades.length} trades · showing {sorted.length}
        </span>
      </div>
      <div className="overflow-x-auto" style={{ maxHeight: 520 }}>
        <table className="w-full text-[11.5px] border-collapse">
          <thead className="sticky top-0" style={{ background: "var(--surface)" }}>
            <tr>
              <th className={`${TH} text-left`}>종목</th>
              <th className={`${TH} text-left`}>섹터</th>
              <th className={`${TH} text-right`} onClick={click("entry_date")}>
                진입일{sort === "entry_date" ? (desc ? "↓" : "↑") : ""}
              </th>
              <th className={`${TH} text-right`} onClick={click("exit_date")}>
                청산일{sort === "exit_date" ? (desc ? "↓" : "↑") : ""}
              </th>
              <th className={`${TH} text-right`} onClick={click("holding_days")}>
                보유일{sort === "holding_days" ? (desc ? "↓" : "↑") : ""}
              </th>
              <th className={`${TH} text-right`} onClick={click("pnl_pct")}>
                %{sort === "pnl_pct" ? (desc ? "↓" : "↑") : ""}
              </th>
              <th className={`${TH} text-right`} onClick={click("pnl")}>
                P&L{sort === "pnl" ? (desc ? "↓" : "↑") : ""}
              </th>
              <th className={`${TH} text-left`}>사유</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((t, i) => (
              <tr
                key={`${t.symbol}-${t.entry_date}-${i}`}
                style={{ borderBottom: "1px solid var(--border-soft)" }}
                className="hover:bg-[color:var(--surface-2)]"
              >
                <td className="py-1 px-2">
                  <div className="text-[11.5px]">{t.name}</div>
                  <span className="mono text-[10px] text-[color:var(--fg-muted)]">{t.symbol}</span>
                </td>
                <td className="py-1 px-2 text-[color:var(--fg-muted)] text-[11px]">{t.sector}</td>
                <td className={NUM}>{t.entry_date}</td>
                <td className={NUM}>{t.exit_date}</td>
                <td className={NUM}>{t.holding_days}</td>
                <td className={NUM} style={{ color: tone(t.pnl_pct) }}>
                  {signedPct(t.pnl_pct)}
                </td>
                <td className={NUM} style={{ color: tone(t.pnl) }}>
                  {t.pnl >= 0 ? "+" : ""}
                  {Math.round(t.pnl).toLocaleString()}
                </td>
                <td className="py-1 px-2">
                  <span
                    className={`inline-block px-1.5 py-[1px] text-[10px] rounded border ${exitBadge(t.exit_reason)}`}
                  >
                    {t.exit_reason}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
