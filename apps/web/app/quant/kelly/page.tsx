// Quant · Kelly / 포지션 사이징 (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { KELLY_KPI } from "@/lib/quant/mockData";

export default function KellyPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Kelly Criterion", current: true }]}
        title="Kelly / 포지션 사이징"
        meta="최적 베팅 사이즈 · FRACTIONAL KELLY"
      />
      <DenseSummary cells={KELLY_KPI} />
    </>
  );
}
