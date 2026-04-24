"use client";

import { fmtPct } from "@/lib/format";
import type { TodayLeader } from "@/types/today";
import { cleanSurrogates, pctColor } from "./helpers";

export function TopLeadersList({ rows }: { rows: TodayLeader[] }) {
  return (
    <ul className="flex flex-col">
      {rows.slice(0, 8).map((l, i) => (
        <li
          key={l.symbol}
          className="flex items-center justify-between py-1.5 px-1 text-[12px]"
          style={{ borderBottom: "1px solid var(--border-soft)" }}
        >
          <span className="flex items-baseline gap-2 truncate">
            <span className="mono text-[10px] text-[color:var(--fg-muted)] w-4 inline-block">
              {i + 1}.
            </span>
            <span className="mono">{l.symbol}</span>
            <span className="truncate max-w-[14ch]">
              {cleanSurrogates(l.name)}
            </span>
            {l.trend_template && (
              <span className="mono text-[9.5px] text-[color:var(--muted)]">
                TT {l.trend_template}
              </span>
            )}
          </span>
          <span className="flex items-center gap-3">
            {l.leader_score != null && (
              <span className="mono text-[11px] text-[color:var(--fg-muted)]">
                {l.leader_score.toFixed(2)}
              </span>
            )}
            <span
              className="mono text-[11px] w-14 text-right"
              style={{ color: pctColor(l.d1) }}
            >
              {fmtPct(l.d1, 2)}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}
