// Quant · Portfolio — equal-weight + factor IC views.

import { fetchEnvelope } from "@/lib/api";
import { SmartBetaHeatmap } from "@/components/quant/SmartBetaHeatmap";
import { ICBar } from "@/components/quant/ICBar";
import type { SmartBetaResponse, ICResponse } from "@/types/quant";

const FACTORS = ["momentum", "value", "quality", "low_vol"] as const;

export default async function QuantPortfolioPage() {
  const [holding, ...ics] = await Promise.all([
    fetchEnvelope<SmartBetaResponse>(`/api/v1/quant/smart_beta?variant=equal_weight&n=20`),
    ...FACTORS.map((f) =>
      fetchEnvelope<ICResponse>(`/api/v1/quant/ic?factor=${f}&period=6m&as_of=2025-04-17`),
    ),
  ]);
  return (
    <div className="space-y-6">
      <header>
        <h1 className="display text-3xl">Portfolio & IC</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">
          Equal-weight composite · 6-month factor IC on ky.db
        </p>
      </header>
      <SmartBetaHeatmap holdings={holding.holdings} variant="equal_weight" />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {ics.map((ic) => (
          <ICBar key={ic.factor} ic={ic} />
        ))}
      </div>
    </div>
  );
}
