// Value · EV/EBITDA — cheapest on a cash-flow basis.

import { fetchEnvelope } from "@/lib/api";
import { LeaderList } from "@/components/value/LeaderList";
import type { LeaderListResponse } from "@/types/value";

export default async function ValueEvEbitdaPage() {
  const data = await fetchEnvelope<LeaderListResponse>("/api/v1/value/evebitda?n=30");
  return (
    <LeaderList
      rows={data.rows}
      title="EV / EBITDA"
      subtitle={`저평가 상위 · as of ${data.as_of}`}
      metricKey="ev_ebitda"
      metricHeader="EV/EBITDA"
      metricDigits={2}
    />
  );
}
