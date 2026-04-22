// Quant · Risk Parity — KPI + stub (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { StubCard } from "@/components/shared/StubCard";
import { RISKPARITY_KPI } from "@/lib/quant/mockData";

export default function RiskParityPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Risk Parity", current: true }]}
        title="Risk Parity 포트폴리오"
        meta="각 자산 동일 리스크 기여 · BRIDGEWATER ALL WEATHER"
      />
      <DenseSummary cells={RISKPARITY_KPI} />
      <div style={{ marginTop: 14 }}>
        <StubCard
          icon="⚖"
          title="Risk Parity 배분"
          desc="주식 22%, 채권 46%, 원자재 12%, 금 14%, 현금 6% (변동성 역수 가중). Bridgewater All Weather 스타일."
        />
      </div>
    </>
  );
}
