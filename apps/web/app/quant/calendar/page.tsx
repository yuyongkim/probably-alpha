// Quant · Calendar Effects — seasonality KPI (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { CALENDAR_KPI } from "@/lib/quant/mockData";

export default function CalendarPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Calendar Effects", current: true }]}
        title="Calendar Effects"
        meta="월별 · 요일 · 실적 시즌"
      />
      <DenseSummary cells={CALENDAR_KPI} />
    </>
  );
}
