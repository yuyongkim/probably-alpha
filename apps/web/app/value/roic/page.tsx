// Value · ROIC / FCF Yield — dense KPI + real top-N table.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { LeaderTable } from "@/components/value/LeaderTable";
import type { LeaderListResponse } from "@/types/value";
import { ROIC_KPI } from "@/lib/value/mockData";

export const revalidate = 300;

const pct = (v: unknown) => (typeof v === "number" ? `${(v * 100).toFixed(2)}%` : "—");

export default async function ValueRoicPage({
  searchParams,
}: {
  searchParams: Promise<{ mode?: string }>;
}) {
  const { mode = "roic" } = await searchParams;
  const data = await fetchEnvelope<LeaderListResponse>(`/api/v1/value/roic?n=30&mode=${mode}`);
  const metricKey = mode === "fcf_yield" ? "fcf_yield" : "roic";
  const metricHeader = mode === "fcf_yield" ? "FCF Yield" : "ROIC";
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "ROIC / FCF Yield", current: true }]}
        title="ROIC / FCF Yield 스크리너"
        meta={`자본효율성 + 현금창출력 · ${metricHeader} 정렬 · ?mode=roic|fcf_yield`}
      />
      <DenseSummary cells={ROIC_KPI} />
      <Panel title={`Quality Compounders — Top ${data.rows.length}`} muted={`${metricHeader} 상위 · as of ${data.as_of}`} bodyPadding="p0">
        <LeaderTable rows={data.rows} metricKey={metricKey} metricHeader={metricHeader} metricFormat={pct} highlightPositive />
      </Panel>
    </>
  );
}
