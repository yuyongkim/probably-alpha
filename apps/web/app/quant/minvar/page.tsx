// Quant · Minimum Variance — stub (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function MinVarPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Minimum Variance", current: true }]}
        title="Minimum Variance 포트폴리오"
        meta="최소 분산 조합 · COVARIANCE 기반"
      />
      <StubCard
        icon="∑"
        title="Ledoit-Wolf 수축 추정"
        desc='공분산 수축 추정으로 안정성 확보. 저변동성 종목 자동 가중. 경제학적으로 "Free lunch"에 가장 가까운 전략.'
      />
    </>
  );
}
