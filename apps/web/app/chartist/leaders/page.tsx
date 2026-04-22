// Chartist · Leaders — all-in-one leader board.
import { fetchEnvelope } from "@/lib/api";
import type { LeadersResponse } from "@/types/chartist";
import { LeadersTable } from "@/components/chartist/leaders/LeadersTable";

export const revalidate = 60;

export default async function ChartistLeadersPage() {
  const r = await fetchEnvelope<LeadersResponse>(
    "/api/v1/chartist/leaders?limit=142"
  );
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <h1 className="display text-3xl">Leaders</h1>
          <div className="text-xs text-[color:var(--fg-muted)] mt-1">
            KRX · {r.as_of} CLOSE · SEPA LENS · {r.universe_size.toLocaleString()} UNIVERSE · {r.count} ranked
          </div>
        </div>
      </div>
      <LeadersTable rows={r.rows} />
    </div>
  );
}
