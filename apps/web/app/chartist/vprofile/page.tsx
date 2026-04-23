// Chartist · Volume Profile — real 60D VPVR scan from ky.db.
import { fetchEnvelope } from "@/lib/api";
import type { VProfileResponse } from "@/types/chartist";
import { VProfileView } from "@/components/chartist/vprofile/VProfileView";

export const revalidate = 60;

export default async function ChartistVProfilePage() {
  const data = await fetchEnvelope<VProfileResponse>(
    "/api/v1/chartist/vprofile?limit=800",
  );
  return <VProfileView data={data} />;
}
