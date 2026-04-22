// Quant · Monte Carlo — stub (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function MonteCarloPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Monte Carlo", current: true }]}
        title="Monte Carlo 시뮬레이션"
        meta="10,000 PATHS · VAR · 최종 자산 분포"
      />
      <StubCard
        icon="⊿"
        title="경로 시뮬레이션"
        desc="내 전략의 10,000 경로 시뮬레이션. VaR/CVaR, 최종 자산 분포 (5/50/95 percentile), 최대 drawdown 분포."
      />
    </>
  );
}
