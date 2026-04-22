// Quant · PIT 재무 — default to Samsung; symbol overridable via query string.

import { fetchEnvelope } from "@/lib/api";
import { PITTimeline } from "@/components/quant/PITTimeline";
import type { PITResponse } from "@/types/quant";

export default async function QuantPITPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string }>;
}) {
  const { symbol = "005930" } = await searchParams;
  const pit = await fetchEnvelope<PITResponse>(`/api/v1/quant/pit/${symbol}`);
  return (
    <div className="space-y-4">
      <header>
        <h1 className="display text-3xl">Point-in-Time 재무</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">look-ahead bias 방지 · ?symbol=005930</p>
      </header>
      <PITTimeline pit={pit} />
    </div>
  );
}
