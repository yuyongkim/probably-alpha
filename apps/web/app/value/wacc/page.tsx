// Value · WACC — dense mockup port: KPI + WACC breakdown tables (real).

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { WACCBreakdown } from "@/components/value/WACCBreakdown";
import type { WaccResponse } from "@/types/value";

export const revalidate = 300;

const pct = (v?: number | null, d = 2) => (v == null ? "—" : `${(v * 100).toFixed(d)}%`);

export default async function ValueWaccPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string; beta?: string }>;
}) {
  const { symbol = "005930", beta = "1.0" } = await searchParams;
  const w = await fetchEnvelope<WaccResponse>(`/api/v1/value/wacc/${symbol}?beta=${beta}`);
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "WACC 계산기", current: true }]}
        title="WACC 계산기"
        meta="자기자본비율 · 부채비율 · 세율 · CAPM · KR 10Y 기준"
      />
      <DenseSummary
        cells={[
          { label: "WACC", value: pct(w.wacc), delta: w.fallback ? "50/50 fallback" : "CAPM", tone: "pos" },
          { label: "Cost of Equity", value: pct(w.cost_of_equity), delta: `β ${w.beta}` },
          { label: "After-tax Rd", value: pct(w.cost_of_debt_after_tax), delta: "debt leg" },
          { label: "Rf (KR 10Y)", value: pct(w.rf), delta: "baseline" },
          { label: "Equity Weight", value: pct(w.w_equity, 1), delta: "market cap" },
          { label: "Debt Weight", value: pct(w.w_debt, 1), delta: "net debt" },
        ]}
      />
      <WACCBreakdown wacc={w} />
    </>
  );
}
