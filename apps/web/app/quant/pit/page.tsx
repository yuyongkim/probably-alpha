// Quant · PIT 재무 — Look-ahead bias 방지 엔진, 공시일 기준.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { PITTimeline } from "@/components/quant/PITTimeline";
import type { PITResponse } from "@/types/quant";

export const revalidate = 300;

export default async function QuantPITPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string }>;
}) {
  const { symbol = "005930" } = await searchParams;
  const pit = await fetchEnvelope<PITResponse>(`/api/v1/quant/pit/${symbol}`);
  const ttm = pit.ttm;
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "PIT 재무 엔진", current: true }]}
        title="PIT 재무 엔진"
        meta={`POINT-IN-TIME · 공시일 기준 · ${pit.meta?.name ?? symbol}`}
      />
      <DenseSummary
        cells={[
          { label: "Symbol", value: pit.symbol, delta: pit.meta?.sector ?? "—" },
          { label: "Period End", value: ttm?.period_end ?? "—", delta: `TTM (${ttm?.n_quarters ?? 0} Q)` },
          { label: "Revenue TTM", value: ttm?.revenue_ttm ? (ttm.revenue_ttm / 1e12).toFixed(2) + "조" : "—", delta: "매출" },
          { label: "Net Income TTM", value: ttm?.net_income_ttm ? (ttm.net_income_ttm / 1e12).toFixed(2) + "조" : "—", delta: "순이익" },
          { label: "Equity", value: ttm?.total_equity ? (ttm.total_equity / 1e12).toFixed(2) + "조" : "—", delta: "자본총계" },
          { label: "Source", value: ttm?.source ?? "—", delta: pit.as_of },
        ]}
      />
      <Panel title="재무 시계열 (PIT)" muted="look-ahead bias 방지 · ?symbol=005930">
        <PITTimeline pit={pit} />
      </Panel>
    </>
  );
}
