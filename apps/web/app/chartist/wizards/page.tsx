// Chartist · Wizards — 6 preset overview.
import { fetchEnvelope } from "@/lib/api";
import type { WizardsOverview as WizardsOverviewT } from "@/types/chartist";
import { WizardsOverview } from "@/components/chartist/wizards/WizardsOverview";

export const revalidate = 60;

export default async function ChartistWizardsPage() {
  const r = await fetchEnvelope<WizardsOverviewT>("/api/v1/chartist/wizards");
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <h1 className="display text-3xl">Market Wizards</h1>
          <div className="text-xs text-[color:var(--fg-muted)] mt-1">
            KRX · {r.as_of} CLOSE · 6 프리셋 · 유니버스 {r.universe_size.toLocaleString()}
          </div>
        </div>
      </div>
      <WizardsOverview data={r} />
    </div>
  );
}
