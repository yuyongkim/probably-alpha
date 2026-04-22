// Quant · Pair Trading — cointegration Z-score pair list (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { PairsTable } from "@/components/quant/PairsTable";
import { PAIRS_KPI, PAIRS_ROWS } from "@/lib/quant/mockData";

export default function PairsPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Pair Trading", current: true }]}
        title="Pair Trading · Stat Arb"
        meta="COINTEGRATION · Z-SCORE · MARKET NEUTRAL"
      />
      <DenseSummary cells={PAIRS_KPI} />
      <Panel title="활성 페어 목록" muted="Z-score · Half-life · P-value" bodyPadding="p0">
        <PairsTable rows={PAIRS_ROWS} />
      </Panel>
    </>
  );
}
