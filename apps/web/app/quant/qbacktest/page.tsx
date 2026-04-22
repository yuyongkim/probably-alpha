// Quant · 전략 백테스트 — stub (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function QBacktestPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "전략 백테스트", current: true }]}
        title="전략 백테스트"
        meta="Factor · Macro · Custom"
      />
      <StubCard
        icon="B"
        title="범용 백테스트 엔진"
        desc="비용/슬리피지 반영, IS/OOS 분리, 워크포워드, 파라미터 변경 이력 추적."
      />
    </>
  );
}
