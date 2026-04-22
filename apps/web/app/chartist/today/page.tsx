// Chartist · Today — server component; assembly only (CONTRIBUTING §1).
import { fetchEnvelope } from "@/lib/api";
import type { TodayBundle } from "@/types/chartist";
import { MarketStrip } from "@/components/chartist/today/MarketStrip";
import { SummaryCards } from "@/components/chartist/today/SummaryCards";
import { TopLeadersTable } from "@/components/chartist/today/TopLeadersTable";
import { TopSectorsList } from "@/components/chartist/today/TopSectorsList";

export const revalidate = 60;

export default async function ChartistTodayPage() {
  const bundle = await fetchEnvelope<TodayBundle>("/api/v1/chartist/today");

  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <h1 className="display text-3xl">오늘의 주도주</h1>
          <div className="text-xs text-[color:var(--fg-muted)] mt-1">
            KRX · {bundle.date} CLOSE · SEPA LENS · {bundle.universe_size.toLocaleString()} UNIVERSE
          </div>
        </div>
      </div>
      <MarketStrip items={bundle.market} />
      <SummaryCards items={bundle.summary} />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="lg:col-span-2">
          <TopLeadersTable leaders={bundle.leaders} />
        </div>
        <TopSectorsList sectors={bundle.sectors} />
      </div>
    </div>
  );
}
