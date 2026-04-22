// Quant · Factors — dense mockup port: market strip, summary, tables, heatmaps, activity.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { FactorsDenseView } from "@/components/quant/FactorsDenseView";
import type { FactorResponse } from "@/types/quant";

export const revalidate = 60;

export default async function QuantFactorsPage() {
  const data = await fetchEnvelope<FactorResponse>("/api/v1/quant/factors?limit=100");
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "팩터 스크리너", current: true }]}
        title="팩터 스크리너"
        meta={`VALUE · QUALITY · MOMENTUM · LOW-VOL · GROWTH · SIZE · ${data.as_of} EOD`}
        subNav={[
          { label: "Composite", active: true },
          { label: "Value" },
          { label: "Quality" },
          { label: "Momentum" },
          { label: "Low-Vol" },
          { label: "Long-Short" },
        ]}
      />
      <FactorsDenseView rows={data.rows} />
    </>
  );
}
