// Value · EV/EBITDA — dense table (real).

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { LeaderTable } from "@/components/value/LeaderTable";
import type { LeaderListResponse } from "@/types/value";

export const revalidate = 300;

export default async function ValueEvEbitdaPage() {
  const data = await fetchEnvelope<LeaderListResponse>("/api/v1/value/evebitda?n=30");
  const evValues = data.rows
    .map((r) => (typeof r.ev_ebitda === "number" ? (r.ev_ebitda as number) : null))
    .filter((v): v is number => v != null);
  const median = evValues.length ? evValues[Math.floor(evValues.length / 2)] : 0;
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "EV / EBITDA", current: true }]}
        title="EV / EBITDA 스크리너"
        meta="부채 보정된 밸류에이션 · PER 대비 우월"
      />
      <DenseSummary
        cells={[
          { label: "Universe", value: String(data.rows.length), delta: "Top 30" },
          { label: "Median EV/EBITDA", value: median.toFixed(2), delta: "Cheapest half" },
          { label: "Lowest", value: evValues[0]?.toFixed(2) ?? "—", delta: "Bargain", tone: "pos" },
          { label: "Highest", value: evValues[evValues.length - 1]?.toFixed(2) ?? "—", delta: "Premium" },
          { label: "as of", value: data.as_of, delta: "ky.db" },
          { label: "Mode", value: data.mode ?? "default", delta: "real" },
        ]}
      />
      <Panel title={`EV/EBITDA 저평가 Top ${data.rows.length}`} muted={`as of ${data.as_of}`} bodyPadding="p0">
        <LeaderTable rows={data.rows} metricKey="ev_ebitda" metricHeader="EV/EBITDA" metricDigits={2} />
      </Panel>
    </>
  );
}
