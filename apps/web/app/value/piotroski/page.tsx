// Value · Piotroski — single symbol breakdown, default Samsung.

import { fetchEnvelope } from "@/lib/api";
import { PiotroskiBreakdown } from "@/components/value/PiotroskiBreakdown";
import type { PiotroskiResponse } from "@/types/value";

export default async function ValuePiotroskiPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string }>;
}) {
  const { symbol = "005930" } = await searchParams;
  const p = await fetchEnvelope<PiotroskiResponse>(
    `/api/v1/value/piotroski?symbol=${symbol}`,
  );
  return (
    <div className="space-y-4">
      <header>
        <h1 className="display text-3xl">Piotroski F-Score</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">?symbol=005930</p>
      </header>
      <PiotroskiBreakdown p={p} />
    </div>
  );
}
