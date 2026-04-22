// Value · Dividend — 배당주 스크리너 (stub).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function ValueDividendPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "배당주 스크리너", current: true }]}
        title="배당주 스크리너"
        meta="YIELD · PAYOUT · GROWTH"
      />
      <StubCard
        icon="D"
        title="배당 귀족주"
        desc="10년 연속 배당 성장, 배당성향 40-70%, 시가배당률 순위."
      />
    </>
  );
}
