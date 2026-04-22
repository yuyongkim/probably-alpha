// Value · Deep Value — low PB + low PEG screen.

import { fetchEnvelope } from "@/lib/api";
import { LeaderList } from "@/components/value/LeaderList";
import type { LeaderListResponse } from "@/types/value";

export default async function ValueDeepValuePage() {
  const data = await fetchEnvelope<LeaderListResponse>("/api/v1/value/deep_value?n=30");
  return (
    <LeaderList
      rows={data.rows}
      title="Deep Value"
      subtitle={`P/B < 1 · PEG < 1 · as of ${data.as_of}`}
      metricKey="pb"
      metricHeader="P/B proxy"
      metricDigits={3}
    />
  );
}
