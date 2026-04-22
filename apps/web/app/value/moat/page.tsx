// Value · Moat — Wide Moat 종목 테이블 (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { MoatTable } from "@/components/value/MoatTable";
import { MOAT_KPI, MOAT_ROWS } from "@/lib/value/mockData";

export default function ValueMoatPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "경제적 해자", current: true }]}
        title="경제적 해자 분석 (Moat)"
        meta="MORNINGSTAR-STYLE · NETWORK · SWITCHING · SCALE · BRAND · IP"
      />
      <DenseSummary cells={MOAT_KPI} />
      <Panel title="Wide Moat 종목" muted="해자 소스 + 지속성 평가" bodyPadding="p0">
        <MoatTable rows={MOAT_ROWS} />
      </Panel>
    </>
  );
}
