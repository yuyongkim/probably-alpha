// Chartist · Patterns — real VCP/Cup&Handle/Flat Base/Asc Triangle scan from ky.db.
import { fetchEnvelope } from "@/lib/api";
import type { PatternsResponse } from "@/types/chartist";
import { PatternsView } from "@/components/chartist/patterns/PatternsView";

export const revalidate = 60;

export default async function ChartistPatternsPage() {
  const data = await fetchEnvelope<PatternsResponse>(
    "/api/v1/chartist/patterns?limit=800",
  );
  return <PatternsView data={data} />;
}
