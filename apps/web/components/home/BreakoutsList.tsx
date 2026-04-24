"use client";

import { fmtPct } from "@/lib/format";
import type { TodayBreakout } from "@/types/today";
import { cleanSurrogates } from "./helpers";

export function BreakoutsList({ rows }: { rows: TodayBreakout[] }) {
  return (
    <ul className="flex flex-col">
      {rows.map((b) => (
        <li
          key={b.symbol}
          className="flex items-center justify-between py-1 px-1 text-[11.5px]"
          style={{ borderBottom: "1px solid var(--border-soft)" }}
        >
          <span className="flex items-baseline gap-2 truncate">
            <span className="mono">{b.symbol}</span>
            <span className="truncate max-w-[10ch]">
              {cleanSurrogates(b.ticker)}
            </span>
          </span>
          <span className="flex items-baseline gap-2">
            <span className="mono text-[11px]" style={{ color: "var(--pos)" }}>
              {fmtPct(b.pct_up, 2)}
            </span>
            {b.vol_x != null && (
              <span className="mono text-[10px] text-[color:var(--fg-muted)]">
                ×{b.vol_x.toFixed(1)}
              </span>
            )}
          </span>
        </li>
      ))}
    </ul>
  );
}
