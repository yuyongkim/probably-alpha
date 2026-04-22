// Quant · 실행 기록 — 백테스트 히스토리 테이블 (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { Panel } from "@/components/shared/Panel";
import { RUNS_ROWS } from "@/lib/quant/mockData";

export default function RunsPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "실행 기록", current: true }]}
        title="백테스트 실행 기록"
        meta="RUN HISTORY"
      />
      <Panel bodyPadding="p0">
        <table className="plain">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Strategy</th>
              <th>Period</th>
              <th className="num">CAGR</th>
              <th className="num">MDD</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {RUNS_ROWS.map((r) => (
              <tr key={r.runId}>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{r.runId}</td>
                <td>{r.strategy}</td>
                <td>{r.period}</td>
                <td className="num" style={{ color: "var(--pos)" }}>{r.cagr}</td>
                <td className="num">{r.mdd}</td>
                <td><span className="chip pos">{r.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </>
  );
}
