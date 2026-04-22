// Quant · Academic — 4 strategy cards (Magic Formula / Deep Value / Fast Growth / Super Quant).

import { fetchEnvelope } from "@/lib/api";
import { AcademicStrategyCards } from "@/components/quant/AcademicStrategyCards";
import type { AcademicResponse } from "@/types/quant";

const STRATEGIES: Array<[string, string, string]> = [
  ["magic_formula", "magic_score", "Magic"],
  ["deep_value", "pb_proxy", "P/B proxy"],
  ["fast_growth", "score", "Growth"],
  ["super_quant", "super_score", "Super"],
];

export default async function QuantAcademicPage() {
  const bundles = await Promise.all(
    STRATEGIES.map(([s]) => fetchEnvelope<AcademicResponse>(`/api/v1/quant/academic/${s}?n=15`)),
  );
  return (
    <div className="space-y-6">
      <header>
        <h1 className="display text-3xl">Academic Strategies</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">
          Greenblatt · Graham · Growth · Composite — ky.db 기반
        </p>
      </header>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {bundles.map((b, i) => (
          <AcademicStrategyCards
            key={STRATEGIES[i][0]}
            strategy={b.strategy}
            rows={b.rows}
          />
        ))}
      </div>
    </div>
  );
}
