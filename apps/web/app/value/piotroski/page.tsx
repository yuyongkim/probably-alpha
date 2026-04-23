// Value · Piotroski — dense KPI + single-symbol breakdown (real).

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { PiotroskiBreakdown } from "@/components/value/PiotroskiBreakdown";
import type { PiotroskiResponse } from "@/types/value";
import { PIOTROSKI_KPI } from "@/lib/value/mockData";

export const revalidate = 300;

export default async function ValuePiotroskiPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string }>;
}) {
  const { symbol = "005930" } = await searchParams;
  // Prefer the 9/9-flag derived calc; fall back to the legacy 5-flag
  // endpoint when the derived path returns no data.
  let p: PiotroskiResponse;
  try {
    p = await fetchEnvelope<PiotroskiResponse>(
      `/api/v1/value/piotroski_full/${symbol}`,
    );
  } catch {
    p = await fetchEnvelope<PiotroskiResponse>(
      `/api/v1/value/piotroski?symbol=${symbol}`,
    );
  }
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "Piotroski F-Score", current: true }]}
        title="Piotroski F-Score 9"
        meta={`FINANCIAL STRENGTH SCORING · JOSEPH PIOTROSKI · ${symbol}`}
      />
      <DenseSummary cells={PIOTROSKI_KPI} />
      <Panel title={`F-Score Breakdown — ${symbol}`} muted={`${p.score}/${p.max_possible} (as of ${p.as_of})`}>
        <PiotroskiBreakdown p={p} />
      </Panel>
    </>
  );
}
