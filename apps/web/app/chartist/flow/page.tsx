// Chartist · Flow — 수급 대시보드 (real data from fnguide investor_trend).
import { fetchEnvelope } from "@/lib/api";
import type { FlowResponse } from "@/types/chartist";
import { FlowView } from "@/components/chartist/flow/FlowView";

export const revalidate = 60;

export default async function ChartistFlowPage() {
  const data = await fetchEnvelope<FlowResponse>(
    "/api/v1/chartist/flow?days=5&top_foreign=15&top_institution=10",
  );
  return <FlowView data={data} />;
}
