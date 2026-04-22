// Quant · Walk-forward — stub (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function WalkForwardPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "워크포워드", current: true }]}
        title="Walk-forward 분석"
        meta="OOS 검증"
      />
      <StubCard
        icon="W"
        title="롤링 윈도우 성과"
        desc="IS 최적화 → OOS 검증을 시간축으로 반복. 파라미터 안정성 확인."
      />
    </>
  );
}
