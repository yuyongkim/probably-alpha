// Chartist · Ichimoku — real Tenkan/Kijun/Senkou/Chikou scan from ky.db.
import { fetchEnvelope } from "@/lib/api";
import type { IchimokuResponse } from "@/types/chartist";
import { IchimokuView } from "@/components/chartist/ichimoku/IchimokuView";

export const revalidate = 60;

export default async function ChartistIchimokuPage() {
  const data = await fetchEnvelope<IchimokuResponse>(
    "/api/v1/chartist/ichimoku?limit=800",
  );
  return <IchimokuView data={data} />;
}
