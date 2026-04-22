// Value · Trend — 재무 KPI 시계열 (real).

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { FinancialTrend } from "@/components/value/FinancialTrend";
import type { TrendResponse } from "@/types/value";

export const revalidate = 300;

export default async function ValueTrendPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string; n?: string }>;
}) {
  const { symbol = "005930", n = "8" } = await searchParams;
  const t = await fetchEnvelope<TrendResponse>(`/api/v1/value/trend/${symbol}?n=${n}`);
  const last = t.series[0];
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "재무 트렌드 차트", current: true }]}
        title="재무 KPI 시계열"
        meta={`매출 · 영업이익 · ROE · FCF · ${t.meta?.name ?? symbol}`}
      />
      <DenseSummary
        cells={[
          { label: "Symbol", value: t.symbol, delta: t.meta?.sector ?? "—" },
          { label: "Latest Period", value: last?.period_end ?? "—", delta: last?.period_type ?? "—" },
          { label: "Revenue", value: last?.revenue ? `${(last.revenue / 1e12).toFixed(2)}조` : "—", delta: "최근 분기" },
          { label: "OpInc", value: last?.operating_income ? `${(last.operating_income / 1e12).toFixed(2)}조` : "—", delta: "영업이익" },
          { label: "NetInc", value: last?.net_income ? `${(last.net_income / 1e12).toFixed(2)}조` : "—", delta: "순이익" },
          { label: "Periods", value: String(t.series.length), delta: `최근 ${n}분기` },
        ]}
      />
      <Panel title="분기별 재무 지표 추이" muted="ky.db financials_pit">
        <FinancialTrend trend={t} />
      </Panel>
    </>
  );
}
