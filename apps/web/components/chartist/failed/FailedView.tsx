import {
  Breadcrumb,
  PageHeader,
  SummaryRow,
  Panel,
  Chip,
  MINI_TABLE_CLS,
  MINI_TH,
  MINI_TH_NUM,
  MINI_TD,
  MINI_TD_NUM,
  MINI_ROW_BORDER,
} from "@/components/chartist/common/MockupPrimitives";
import { TickerName } from "@/components/shared/TickerName";
import { FAILED_SUMMARY, FAILED_ROWS } from "@/lib/chartist/mockData";

export function FailedView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "실패 돌파 로그"]} />
      <PageHeader title="실패 돌파 로그" meta="POST-MORTEM · LEARNING ARCHIVE" />
      <SummaryRow cells={FAILED_SUMMARY} />
      <Panel title="이번주 실패 돌파" subtitle="사후분석 + 공통 패턴" bodyPad={false}>
        <table className={MINI_TABLE_CLS}>
          <thead>
            <tr>
              <th className={MINI_TH}>Date</th>
              <th className={MINI_TH}>Ticker</th>
              <th className={MINI_TH_NUM}>돌파가</th>
              <th className={MINI_TH_NUM}>최저가</th>
              <th className={MINI_TH_NUM}>손실%</th>
              <th className={MINI_TH}>원인</th>
              <th className={MINI_TH}>교훈</th>
            </tr>
          </thead>
          <tbody>
            {FAILED_ROWS.map((r) => (
              <tr key={r.date + r.name} style={MINI_ROW_BORDER}>
                <td className={`${MINI_TD} mono text-[10.5px]`}>{r.date}</td>
                <td className={MINI_TD}>
                  <TickerName symbol="" name={r.name} />
                </td>
                <td className={MINI_TD_NUM}>{r.bo.toLocaleString()}</td>
                <td className={MINI_TD_NUM}>{r.low.toLocaleString()}</td>
                <td className={MINI_TD_NUM} style={{ color: "var(--neg)" }}>
                  {r.loss.toFixed(1)}%
                </td>
                <td className={MINI_TD}>
                  <Chip tone="neg">{r.cause}</Chip>
                </td>
                <td className={`${MINI_TD} text-[10.5px] text-[color:var(--fg-muted)]`}>
                  {r.lesson}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <div
        className="mt-2 p-3 rounded-md text-[12px] leading-relaxed border-l-2"
        style={{
          background: "var(--accent-soft)",
          borderColor: "var(--accent)",
          color: "var(--fg)",
        }}
      >
        <strong>반복되는 패턴 (30일):</strong> 거래량 확증 부족 (12/24, 50%) &gt; Stage 1
        가짜 돌파 (7/24) &gt; 섹터 약세 동반 (5/24). →{" "}
        <strong>Rule:</strong> Vol &lt; 1.5× or Stage 1 or Sector RS &lt; 0.5
        중 하나라도 걸리면 진입 보류.
      </div>
    </div>
  );
}
