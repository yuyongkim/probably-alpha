// Quant · Corr — macro × sector correlation heatmap (dense).

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { Panel } from "@/components/shared/Panel";
import { CorrTable } from "@/components/quant/CorrTable";
import type { CorrResponse } from "@/types/macro";

export const revalidate = 600;

export default async function CorrPage() {
  const data = await fetchEnvelope<CorrResponse>("/api/v1/quant/macro/corr?window=60");
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "상관관계 히트맵", current: true }]}
        title="Macro ↔ Asset 상관관계"
        meta={`LEAD-LAG · ${data.window}D window${data.warning ? ` · ${data.warning}` : ""}`}
      />
      <Panel title="Macro × Sector (60D)" muted="Daily returns correlation" bodyPadding="tight">
        <CorrTable data={data} />
      </Panel>
    </>
  );
}
