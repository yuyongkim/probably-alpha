// Value · Trend — 8Q financial trend for one symbol.

import { fetchEnvelope } from "@/lib/api";
import { FinancialTrend } from "@/components/value/FinancialTrend";
import type { TrendResponse } from "@/types/value";

export default async function ValueTrendPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string; n?: string }>;
}) {
  const { symbol = "005930", n = "8" } = await searchParams;
  const trend = await fetchEnvelope<TrendResponse>(
    `/api/v1/value/trend/${symbol}?n=${n}`,
  );
  return (
    <div className="space-y-4">
      <header>
        <h1 className="display text-3xl">Financial Trend</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">
          최근 {n}개 분기 · ?symbol=005930&amp;n=8
        </p>
      </header>
      <FinancialTrend trend={trend} />
    </div>
  );
}
