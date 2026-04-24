"use client";

import { fmtPct } from "@/lib/format";
import type { TodaySector } from "@/types/today";
import { cleanSurrogates, pctColor } from "./helpers";

export function TopSectorsList({ rows }: { rows: TodaySector[] }) {
  return (
    <ul className="flex flex-col">
      {rows.slice(0, 8).map((s) => (
        <li
          key={s.name}
          className="flex items-center justify-between py-1.5 px-1 text-[12px]"
          style={{ borderBottom: "1px solid var(--border-soft)" }}
        >
          <span className="flex items-baseline gap-2">
            <span className="mono text-[10px] text-[color:var(--fg-muted)] w-4 inline-block">
              {s.rank}.
            </span>
            <span>{cleanSurrogates(s.name)}</span>
          </span>
          <span className="flex items-center gap-3">
            {s.score != null && (
              <span className="mono text-[11px] text-[color:var(--fg-muted)]">
                {s.score.toFixed(2)}
              </span>
            )}
            <span
              className="mono text-[11px] w-14 text-right"
              style={{ color: pctColor(s.d1) }}
            >
              {fmtPct(s.d1, 2)}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}
