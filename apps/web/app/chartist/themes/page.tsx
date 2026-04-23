// Chartist · Themes — 20 테마 로테이션 (real data from data/themes.yml × panel returns).
import { fetchEnvelope } from "@/lib/api";
import type { ThemesResponse } from "@/types/chartist";
import { ThemesView } from "@/components/chartist/themes/ThemesView";

export const revalidate = 60;

export default async function ChartistThemesPage() {
  const data = await fetchEnvelope<ThemesResponse>(
    "/api/v1/chartist/themes?max_members=8",
  );
  return <ThemesView data={data} />;
}
