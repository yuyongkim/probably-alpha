// Value · Consensus — EPS revision · TP revision · upgrade (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { ConsensusTable } from "@/components/value/ConsensusTable";
import { CONSENSUS_KPI, CONSENSUS_ROWS } from "@/lib/value/mockData";

export default function ValueConsensusPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "애널리스트 컨센서스", current: true }]}
        title="애널리스트 컨센서스"
        meta="EPS REVISION · TARGET PRICE · UPGRADE / DOWNGRADE"
      />
      <DenseSummary cells={CONSENSUS_KPI} />
      <Panel title="EPS Revision Top (1주)" muted="컨센서스 상향 강한 종목" bodyPadding="p0">
        <ConsensusTable rows={CONSENSUS_ROWS} />
      </Panel>
    </>
  );
}
