// Quant · Portfolio Builder — dense KPI + equal-weight composite + factor IC bars.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { SmartBetaHeatmap } from "@/components/quant/SmartBetaHeatmap";
import { ICBar } from "@/components/quant/ICBar";
import type { SmartBetaResponse, ICResponse } from "@/types/quant";

export const revalidate = 60;

const FACTORS = ["momentum", "value", "quality", "low_vol"] as const;

export default async function QuantPortfolioPage() {
  const [holding, ...ics] = await Promise.all([
    fetchEnvelope<SmartBetaResponse>(`/api/v1/quant/smart_beta?variant=equal_weight&n=20`),
    ...FACTORS.map((f) =>
      fetchEnvelope<ICResponse>(`/api/v1/quant/ic?factor=${f}&period=6m&as_of=2025-04-17`),
    ),
  ]);
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "포트폴리오", current: true }]}
        title="포트폴리오 빌더"
        meta="EQUAL-WEIGHT COMPOSITE · 6M FACTOR IC"
      />
      <DenseSummary
        cells={[
          { label: "Holdings", value: String(holding.holdings.length), delta: "equal-weight", tone: "pos" },
          { label: "Variant", value: holding.variant, delta: "smart-beta" },
          { label: "As Of", value: holding.as_of, delta: "ky.db" },
          { label: "Factor IC (6M)", value: "4", delta: "Momentum · Value · Quality · LV" },
          { label: "리밸런싱", value: "월 1회", delta: "자동", tone: "pos" },
          { label: "KIS 자동주문", value: "OFF", delta: "준비 중" },
        ]}
      />
      <Panel title="Equal-Weight Composite" muted={`${holding.holdings.length} holdings · ${holding.as_of}`} style={{ marginBottom: 10 }}>
        <SmartBetaHeatmap holdings={holding.holdings} variant="equal_weight" />
      </Panel>
      <div className="grid-2-equal">
        {ics.map((ic) => (
          <ICBar key={ic.factor} ic={ic} />
        ))}
      </div>
    </>
  );
}
