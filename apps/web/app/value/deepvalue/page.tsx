// Value · Deep Value — dense KPI + real P/B·PEG screener.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { LeaderTable } from "@/components/value/LeaderTable";
import type { LeaderListResponse } from "@/types/value";

export const revalidate = 300;

export default async function ValueDeepValuePage() {
  const data = await fetchEnvelope<LeaderListResponse>("/api/v1/value/deep_value?n=30");
  const pbUnder1 = data.rows.filter((r) => typeof r.pb === "number" && (r.pb as number) < 1).length;
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "Deep Value", current: true }]}
        title="Deep Value 스크리너"
        meta="P/B · PEG · EV/EBITDA · NET-NET"
      />
      <DenseSummary
        cells={[
          { label: "Top N", value: String(data.rows.length), delta: "screened", tone: "pos" },
          { label: "as of", value: data.as_of, delta: "ky.db" },
          { label: "Mode", value: data.mode ?? "default", delta: "" },
          { label: "P/B < 1", value: String(pbUnder1), delta: "count", tone: "pos" },
          { label: "Filter", value: "Graham", delta: "Net-net 호환" },
          { label: "Horizon", value: "Long", delta: "가치 회귀" },
        ]}
      />
      <Panel title={`Deep Value Top ${data.rows.length}`} muted={`P/B · PEG 기준 · as of ${data.as_of}`} bodyPadding="p0">
        <LeaderTable rows={data.rows} metricKey="pb" metricHeader="P/B proxy" metricDigits={3} />
      </Panel>
    </>
  );
}
