// Value · Insider — 내부자 거래 (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { InsiderTable } from "@/components/value/InsiderTable";
import { INSIDER_KPI, INSIDER_ROWS } from "@/lib/value/mockData";

export default function ValueInsiderPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "내부자 거래", current: true }]}
        title="내부자 거래 (DART)"
        meta="임원 · 주요주주 · 최대주주 친인척 · 자발적 거래만"
      />
      <DenseSummary cells={INSIDER_KPI} />
      <Panel title="주목할 내부자 거래" muted="최근 7일" bodyPadding="p0">
        <InsiderTable rows={INSIDER_ROWS} />
      </Panel>
    </>
  );
}
