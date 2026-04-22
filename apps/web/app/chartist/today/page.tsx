// Chartist · Today — server component; assembly only (CONTRIBUTING §1).
import { fetchEnvelope } from "@/lib/api";
import type { TodayBundle } from "@/types/chartist";
import { MarketStrip } from "@/components/chartist/today/MarketStrip";
import { SummaryCards } from "@/components/chartist/today/SummaryCards";
import { TopLeadersTable } from "@/components/chartist/today/TopLeadersTable";
import { TopSectorsList } from "@/components/chartist/today/TopSectorsList";
import { BreakoutsPanel } from "@/components/chartist/today/BreakoutsPanel";
import { SectorHeatmap } from "@/components/chartist/today/SectorHeatmap";
import { WizardsPassCount } from "@/components/chartist/today/WizardsPassCount";
import { StageDistribution } from "@/components/chartist/today/StageDistribution";
import { ActivityLog } from "@/components/chartist/today/ActivityLog";
import { UpcomingEvents } from "@/components/chartist/today/UpcomingEvents";

export const revalidate = 60;

export default async function ChartistTodayPage() {
  const b = await fetchEnvelope<TodayBundle>("/api/v1/chartist/today");
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <h1 className="display text-3xl">오늘의 주도주</h1>
          <div className="text-xs text-[color:var(--fg-muted)] mt-1">
            KRX · {b.date} CLOSE · SEPA LENS · {b.universe_size.toLocaleString()} UNIVERSE
          </div>
        </div>
      </div>
      <MarketStrip items={b.market} />
      <SummaryCards items={b.summary} />
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-3 mb-3">
        <div className="lg:col-span-2"><TopLeadersTable leaders={b.leaders} /></div>
        <TopSectorsList sectors={b.sectors} />
        <BreakoutsPanel items={b.breakouts} />
      </div>
      <SectorHeatmap rows={b.heatmap} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3">
        <WizardsPassCount items={b.wizards_pass} />
        <StageDistribution items={b.stage_dist} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <ActivityLog items={b.activity_log} />
        <UpcomingEvents items={b.upcoming_events} />
      </div>
    </div>
  );
}
