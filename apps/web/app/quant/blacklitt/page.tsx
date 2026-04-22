// Quant · Black-Litterman — stub (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function BlackLittPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Black-Litterman", current: true }]}
        title="Black-Litterman 모델"
        meta="베이지안 기대수익률 · 시장 균형 + 내 견해"
      />
      <StubCard
        icon="Β"
        title="시장 균형 + Subjective Views"
        desc="시장 암묵 기대수익률에서 시작, 내 견해(+ 신뢰도)를 베이지안 결합. 극단적 배분 완화."
      />
    </>
  );
}
