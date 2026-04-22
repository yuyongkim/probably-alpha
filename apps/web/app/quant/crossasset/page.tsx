// Quant · Cross-Asset Momentum — stub card (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function CrossAssetPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Cross-Asset Momentum", current: true }]}
        title="Cross-Asset Momentum"
        meta="주식 · 채권 · 원자재 · 환율"
      />
      <StubCard
        icon="⟷"
        title="4-자산 모멘텀 로테이션"
        desc="주식/채권/원자재/환율 12-1 모멘텀 순위로 배분. Global Tactical Asset Allocation."
      />
    </>
  );
}
