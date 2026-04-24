"use client";

import type { KpiPill } from "@/types/today";
import { toneColor } from "./helpers";

interface Props {
  pill: KpiPill;
  compact?: boolean;
}

export function PillCard({ pill, compact = false }: Props) {
  return (
    <div
      className={`rounded-md border ${compact ? "p-2" : "p-3"}`}
      style={{ borderColor: "var(--border-soft)", background: "var(--bg)" }}
    >
      <div
        className={`text-[10px] uppercase tracking-widest text-[color:var(--muted)] ${compact ? "mb-0.5" : "mb-1"}`}
      >
        {pill.label}
      </div>
      <div className={`mono ${compact ? "text-[13px]" : "text-lg"}`}>
        {pill.value}
      </div>
      {pill.delta && (
        <div
          className="text-[10px] mt-1"
          style={{ color: toneColor(pill.tone) }}
        >
          {pill.delta}
        </div>
      )}
    </div>
  );
}
