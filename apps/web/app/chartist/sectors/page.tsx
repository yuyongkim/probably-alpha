// Chartist · Sectors — 28-sector heatmap + member count.
import { fetchEnvelope } from "@/lib/api";
import type { SectorsResponse } from "@/types/chartist";
import { SectorHeatmap } from "@/components/chartist/sectors/SectorHeatmap";

export const revalidate = 60;

export default async function ChartistSectorsPage() {
  const r = await fetchEnvelope<SectorsResponse>(
    "/api/v1/chartist/sectors?top_n=40"
  );
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <h1 className="display text-3xl">Sectors</h1>
          <div className="text-xs text-[color:var(--fg-muted)] mt-1">
            KRX · {r.as_of} CLOSE · {r.count} 섹터 강도 순위
          </div>
        </div>
      </div>
      <SectorHeatmap rows={r.rows} />
    </div>
  );
}
