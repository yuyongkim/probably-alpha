// Value · Comparables — 동종업계 비교 (stub).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function ValueComparablesPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "동종업계 비교", current: true }]}
        title="Comparables"
        meta="섹터별 상대 밸류에이션"
      />
      <StubCard
        icon="C"
        title="Peer Comparison"
        desc="동종업계 대비 PER/PBR/EV/EBITDA 산점도, 아웃라이어 식별."
      />
    </>
  );
}
