// Chartist · Kiwoom Conditions — 키움 조건식 7종 (real panel scan).
import { fetchEnvelope } from "@/lib/api";
import type { KiwoomCondResponse } from "@/types/chartist";
import { KiwoomCondView } from "@/components/chartist/kiwoom_cond/KiwoomCondView";

export const revalidate = 60;

export default async function ChartistKiwoomCondPage() {
  const data = await fetchEnvelope<KiwoomCondResponse>(
    "/api/v1/chartist/kiwoom_cond?top_per_bucket=30&top_intersection=40",
  );
  return <KiwoomCondView data={data} />;
}
