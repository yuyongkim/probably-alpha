// Value · Margin of Safety — DCF upside leaders.

import { fetchEnvelope } from "@/lib/api";
import { LeaderList } from "@/components/value/LeaderList";
import type { LeaderListResponse } from "@/types/value";

export default async function ValueMoSPage() {
  const data = await fetchEnvelope<LeaderListResponse>("/api/v1/value/mos?n=30");
  return (
    <LeaderList
      rows={data.rows}
      title="Margin of Safety"
      subtitle={`DCF 내재가치 대비 저평가 상위 · as of ${data.as_of}`}
      metricKey="margin_of_safety"
      metricHeader="MoS%"
      metricFormat={(v) =>
        typeof v === "number" ? `${(v * 100).toFixed(1)}%` : "–"
      }
    />
  );
}
