// Quant · Smart Beta — 6 variants in a grid.

import { fetchEnvelope } from "@/lib/api";
import { SmartBetaHeatmap } from "@/components/quant/SmartBetaHeatmap";
import type { SmartBetaResponse } from "@/types/quant";

const VARIANTS = ["low_vol", "quality", "momentum", "equal_weight", "high_div", "qmj"] as const;

export default async function QuantSmartBetaPage() {
  const bundles = await Promise.all(
    VARIANTS.map((v) => fetchEnvelope<SmartBetaResponse>(`/api/v1/quant/smart_beta?variant=${v}&n=15`)),
  );
  return (
    <div className="space-y-6">
      <header>
        <h1 className="display text-3xl">Smart Beta</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">6 index variants · ky.db</p>
      </header>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {bundles.map((b) => (
          <SmartBetaHeatmap key={b.variant} holdings={b.holdings} variant={b.variant} />
        ))}
      </div>
    </div>
  );
}
