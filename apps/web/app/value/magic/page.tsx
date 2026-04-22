// Value · Magic Formula — Greenblatt shortcut (lives under Value too).

import { fetchEnvelope } from "@/lib/api";
import { AcademicStrategyCards } from "@/components/quant/AcademicStrategyCards";
import type { AcademicResponse } from "@/types/quant";

export default async function ValueMagicPage() {
  const data = await fetchEnvelope<AcademicResponse>("/api/v1/quant/academic/magic_formula?n=30");
  return (
    <div className="space-y-4">
      <header>
        <h1 className="display text-3xl">Magic Formula</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">
          Greenblatt · ROC + Earnings Yield 합산 랭크 · as of {data.as_of}
        </p>
      </header>
      <AcademicStrategyCards strategy={data.strategy} rows={data.rows} />
    </div>
  );
}
