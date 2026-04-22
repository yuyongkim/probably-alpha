// Chartist · Breadth — A/D, %>MA, new H/L, McClellan.
import { fetchEnvelope } from "@/lib/api";
import type { BreadthResponse } from "@/types/chartist";
import { BreadthDashboard } from "@/components/chartist/breadth/BreadthDashboard";

export const revalidate = 60;

export default async function ChartistBreadthPage() {
  const r = await fetchEnvelope<BreadthResponse>("/api/v1/chartist/breadth");
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <h1 className="display text-3xl">Breadth</h1>
          <div className="text-xs text-[color:var(--fg-muted)] mt-1">
            KRX · {r.as_of} CLOSE · market-wide participation & McClellan
          </div>
        </div>
      </div>
      <BreadthDashboard data={r} />
    </div>
  );
}
