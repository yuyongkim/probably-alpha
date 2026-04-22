// Value · WACC — CAPM-based WACC for a symbol.

import { fetchEnvelope } from "@/lib/api";
import { WACCBreakdown } from "@/components/value/WACCBreakdown";
import type { WaccResponse } from "@/types/value";

export default async function ValueWaccPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string; beta?: string }>;
}) {
  const { symbol = "005930", beta = "1.0" } = await searchParams;
  const wacc = await fetchEnvelope<WaccResponse>(
    `/api/v1/value/wacc/${symbol}?beta=${beta}`,
  );
  return (
    <div className="space-y-4">
      <header>
        <h1 className="display text-3xl">WACC</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">?symbol=005930&amp;beta=1.0</p>
      </header>
      <WACCBreakdown wacc={wacc} />
    </div>
  );
}
