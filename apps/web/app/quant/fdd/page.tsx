// Quant · FDD 데이터 품질 — mock.

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { StubCard } from "@/components/shared/StubCard";
import { FDD_KPI } from "@/lib/quant/mockData";

export default function FDDPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "FDD 데이터 품질", current: true }]}
        title="Financial Data Diagnostics"
        meta="ANOMALY · MISSING · INCONSISTENCY"
      />
      <DenseSummary cells={FDD_KPI} />
      <div style={{ marginTop: 20 }}>
        <StubCard
          icon="✓"
          title="데이터 품질 알럿 상세"
          desc="QuantDB의 fdd_validator 이식. 각 알럿 종목, 원인, 자동 대응(제외/재수집)."
          chips={["QuantDB 흡수"]}
        />
      </div>
    </>
  );
}
