// Quant · Mean Reversion — RSI(2) / BB 하단 후보 (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { MeanRevTable } from "@/components/quant/MeanRevTable";
import { MEANREV_KPI, MEANREV_ROWS } from "@/lib/quant/mockData";

export default function MeanRevPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Mean Reversion", current: true }]}
        title="Mean Reversion 전략"
        meta="단기 과매도 반등 · RSI(2) · BB 하단 · Z-SCORE"
      />
      <DenseSummary cells={MEANREV_KPI} />
      <Panel title="Mean Reversion 후보 (오늘)" muted="RSI(2) · BB · Z-score" bodyPadding="p0">
        <MeanRevTable rows={MEANREV_ROWS} />
      </Panel>
    </>
  );
}
