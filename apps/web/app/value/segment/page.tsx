// Value · Segment — SOTP 저평가 (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { SEGMENT_KPI, SEGMENT_ROWS } from "@/lib/value/mockData";

export default function ValueSegmentPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "사업부문 분석", current: true }]}
        title="사업부문 (Segment) 분석"
        meta="SOTP · SEGMENT MARGIN · HIDDEN VALUE"
      />
      <DenseSummary cells={SEGMENT_KPI} />
      <Panel title="SOTP 저평가 Top" muted="Sum-of-the-Parts > Market Cap" bodyPadding="p0">
        <table className="mini">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>부문 수</th>
              <th className="num">시총 (조)</th>
              <th className="num">SOTP (조)</th>
              <th className="num">할인율</th>
              <th>핵심 부문</th>
            </tr>
          </thead>
          <tbody>
            {SEGMENT_ROWS.map((r) => (
              <tr key={r.ticker}>
                <td><span className="ticker-name">{r.ticker}</span></td>
                <td className="num">{r.segments}</td>
                <td className="num">{r.mcap}</td>
                <td className="num">{r.sotp}</td>
                <td className="num" style={{ color: "var(--pos)" }}>{r.discount}</td>
                <td>{r.core}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </>
  );
}
