// Chartist · Divergence — real RSI / MACD / OBV divergence scan from ky.db.
import { fetchEnvelope } from "@/lib/api";
import type { DivergenceResponse } from "@/types/chartist";
import { DivergenceView } from "@/components/chartist/divergence/DivergenceView";

export const revalidate = 60;

export default async function ChartistDivergencePage() {
  const data = await fetchEnvelope<DivergenceResponse>(
    "/api/v1/chartist/divergence?limit=500",
  );
  return <DivergenceView data={data} />;
}
