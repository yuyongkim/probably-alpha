"use client";

import type { TodayStage } from "@/types/today";

export function StagesList({ rows }: { rows: TodayStage[] }) {
  return (
    <ul className="flex flex-col">
      {rows.map((s) => (
        <li
          key={s.name}
          className="flex items-center justify-between py-1 px-1 text-[11.5px]"
          style={{ borderBottom: "1px solid var(--border-soft)" }}
        >
          <span className="flex items-baseline gap-2 truncate">
            {s.color_hint && (
              <span
                className="inline-block w-2.5 h-2.5 rounded"
                style={{ background: s.color_hint }}
              />
            )}
            <span className="truncate">{s.name}</span>
          </span>
          <span className="mono text-[11px]">
            {s.count} · {s.pct?.toFixed(1)}%
          </span>
        </li>
      ))}
    </ul>
  );
}
