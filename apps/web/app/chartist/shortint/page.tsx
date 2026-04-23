// Chartist · Short Interest — 공매도/대차 (proxy scan from panel).
import { fetchEnvelope } from "@/lib/api";
import type { ShortIntResponse } from "@/types/chartist";
import { ShortIntView } from "@/components/chartist/shortint/ShortIntView";

export const revalidate = 60;

export default async function ChartistShortIntPage() {
  const data = await fetchEnvelope<ShortIntResponse>(
    "/api/v1/chartist/shortint?top_n=10",
  );
  return <ShortIntView data={data} />;
}
