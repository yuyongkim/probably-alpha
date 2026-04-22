// Quant · Regime — dense 4-state probability view with Compass-driven regime hint.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { RegimeView } from "@/components/quant/RegimeView";
import type { RegimeResponse } from "@/types/macro";

export const revalidate = 300;

export default async function RegimePage() {
  const r = await fetchEnvelope<RegimeResponse>("/api/v1/quant/macro/regime");
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Regime Detection", current: true }]}
        title="Regime Detection (HMM)"
        meta="HIDDEN MARKOV · 4-STATE · VOLATILITY / RETURN CLUSTERING"
      />
      <RegimeView regime={r} />
    </>
  );
}
