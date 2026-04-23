// Chartist · Support/Resistance — real pivot + long-range S/R scan from ky.db.
import { fetchEnvelope } from "@/lib/api";
import type { SupportResponse } from "@/types/chartist";
import { SupportView } from "@/components/chartist/support/SupportView";

export const revalidate = 60;

export default async function ChartistSupportPage() {
  const data = await fetchEnvelope<SupportResponse>(
    "/api/v1/chartist/support?limit=500",
  );
  return <SupportView data={data} />;
}
