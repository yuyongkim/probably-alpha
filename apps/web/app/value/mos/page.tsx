// Value · Margin of Safety — dense KPI + real top-N table.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseQuote } from "@/components/shared/DenseQuote";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { LeaderTable } from "@/components/value/LeaderTable";
import type { LeaderListResponse } from "@/types/value";
import { MOS_KPI } from "@/lib/value/mockData";

export const revalidate = 60;

const fmtPct = (v: unknown) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "—");

export default async function ValueMoSPage() {
  const data = await fetchEnvelope<LeaderListResponse>("/api/v1/value/mos?n=30");
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "Margin of Safety", current: true }]}
        title="Margin of Safety Screener"
        meta="GRAHAM · NET-NET · DCF UPSIDE · DISTRESS DISCOUNT"
      />
      <DenseQuote
        quote="The three most important words in investing: Margin of Safety."
        attribution="Benjamin Graham · The Intelligent Investor"
      />
      <DenseSummary cells={MOS_KPI} />
      <Panel title={`MoS Top ${data.rows.length}`} muted={`Fair Value 대비 할인율 · as of ${data.as_of}`} bodyPadding="p0">
        <LeaderTable rows={data.rows} metricKey="margin_of_safety" metricHeader="MoS%" metricFormat={fmtPct} highlightPositive />
      </Panel>
    </>
  );
}
