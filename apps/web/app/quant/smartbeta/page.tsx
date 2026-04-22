// Quant · Smart Beta — dense KPI + heatmap + real holdings for the selected variant.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { Heatmap } from "@/components/shared/Heatmap";
import { SmartBetaHeatmap } from "@/components/quant/SmartBetaHeatmap";
import type { SmartBetaResponse } from "@/types/quant";
import { SMARTBETA_KPI, SMARTBETA_HEATMAP } from "@/lib/quant/mockData";

export const revalidate = 60;

export default async function QuantSmartBetaPage({
  searchParams,
}: {
  searchParams: Promise<{ variant?: string }>;
}) {
  const { variant = "low_vol" } = await searchParams;
  const data = await fetchEnvelope<SmartBetaResponse>(
    `/api/v1/quant/smart_beta?variant=${variant}&n=20`,
  );
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Smart Beta", current: true }]}
        title="Smart Beta 전략"
        meta="LOW VOL · QUALITY · VALUE · MOMENTUM · DIVIDEND · EQUAL WEIGHT"
      />
      <DenseSummary cells={SMARTBETA_KPI} />
      <Panel
        title="Smart Beta × 기간 성과"
        muted="KOSPI 대비 초과수익"
        bodyPadding="tight"
        style={{ marginBottom: 10 }}
      >
        <Heatmap
          firstColumnWidth="150px"
          columnHeaders={SMARTBETA_HEATMAP.columns}
          rowLabel="Strategy"
          rows={SMARTBETA_HEATMAP.rows.map((r) => ({
            name: r.name,
            cells: r.cells.map(([value, level]) => ({ value, level })),
          }))}
        />
      </Panel>
      <SmartBetaHeatmap holdings={data.holdings} variant={data.variant} />
    </>
  );
}
