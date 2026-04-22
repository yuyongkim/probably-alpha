// Quant · ML Factor (XGBoost · LSTM) — KPI + stub (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { StubCard } from "@/components/shared/StubCard";
import { MLFACTOR_KPI } from "@/lib/quant/mockData";

export default function MLFactorPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "ML 팩터", current: true }]}
        title="ML 팩터 (XGBoost · LSTM)"
        meta="MACHINE LEARNING · FEATURE IMPORTANCE · OOS VALIDATION"
      />
      <DenseSummary cells={MLFACTOR_KPI} />
      <div style={{ marginTop: 14 }}>
        <StubCard
          icon="⚙"
          title="ML 모델 대시보드"
          desc="Feature importance bar chart, SHAP values, OOS vs IS 수익률, 레짐별 성과 분해."
        />
      </div>
    </>
  );
}
