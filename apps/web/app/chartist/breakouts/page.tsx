// Chartist · Breakouts — 52-week breakouts with volume gate.
import { fetchEnvelope } from "@/lib/api";
import type { BreakoutsResponse } from "@/types/chartist";
import { BreakoutsTable } from "@/components/chartist/breakouts/BreakoutsTable";

export const revalidate = 60;

export default async function ChartistBreakoutsPage() {
  const r = await fetchEnvelope<BreakoutsResponse>(
    "/api/v1/chartist/breakouts/52w?vol_x_min=1.5&limit=100"
  );
  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <h1 className="display text-3xl">Breakouts</h1>
          <div className="text-xs text-[color:var(--fg-muted)] mt-1">
            KRX · {r.as_of} CLOSE · 52주 신고가 돌파 (거래량 확인 포함)
          </div>
        </div>
      </div>
      <BreakoutsTable rows={r.rows} />
    </div>
  );
}
