"use client";

import type { TodayWizard } from "@/types/today";
import { pctColor } from "./helpers";

export function WizardsList({ rows }: { rows: TodayWizard[] }) {
  return (
    <ul className="flex flex-col">
      {rows.map((w) => (
        <li
          key={w.name}
          className="flex items-center justify-between py-1 px-1 text-[11.5px]"
          style={{ borderBottom: "1px solid var(--border-soft)" }}
        >
          <span className="truncate">{w.name}</span>
          <span className="flex items-baseline gap-2">
            <span className="mono">
              {w.pass_count}/{w.total}
            </span>
            {w.delta_vs_yesterday != null && w.delta_vs_yesterday !== 0 && (
              <span
                className="mono text-[10px]"
                style={{ color: pctColor(w.delta_vs_yesterday) }}
              >
                {w.delta_vs_yesterday > 0 ? "+" : ""}
                {w.delta_vs_yesterday}
              </span>
            )}
          </span>
        </li>
      ))}
    </ul>
  );
}
