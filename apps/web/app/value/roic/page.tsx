// Value · ROIC / FCF Yield — Quality Compounders.

import { fetchEnvelope } from "@/lib/api";
import { LeaderList } from "@/components/value/LeaderList";
import type { LeaderListResponse } from "@/types/value";

export default async function ValueRoicPage({
  searchParams,
}: {
  searchParams: Promise<{ mode?: string }>;
}) {
  const { mode = "roic" } = await searchParams;
  const data = await fetchEnvelope<LeaderListResponse>(
    `/api/v1/value/roic?n=30&mode=${mode}`,
  );
  const isFcf = mode === "fcf_yield";
  return (
    <LeaderList
      rows={data.rows}
      title={isFcf ? "FCF Yield" : "ROIC"}
      subtitle={`Quality compounders · as of ${data.as_of} · ?mode=roic|fcf_yield`}
      metricKey={isFcf ? "fcf_yield" : "roic"}
      metricHeader={isFcf ? "FCF Yield" : "ROIC"}
      metricFormat={(v) =>
        typeof v === "number" ? `${(v * 100).toFixed(2)}%` : "–"
      }
    />
  );
}
