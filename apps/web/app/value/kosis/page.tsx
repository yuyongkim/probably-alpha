// Value · KOSIS — 정부 통계 (stub).

import { PageHeader } from "@/components/shared/PageHeader";
import { StubCard } from "@/components/shared/StubCard";

export default function ValueKosisPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "KOSIS 통계", current: true }]}
        title="정부 통계 (KOSIS)"
        meta="경제지표 · 산업통계"
      />
      <StubCard
        icon="⊡"
        title="KOSIS API 통합"
        desc="Finance_analysis의 kosis_api_system 이식. 메타데이터 자동 해석, JSONP 파싱, 응답 캐싱."
        chips={["Finance_analysis 흡수"]}
      />
    </>
  );
}
