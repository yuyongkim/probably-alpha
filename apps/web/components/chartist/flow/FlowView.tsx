import {
  Breadcrumb,
  PageHeader,
  SummaryRow,
  Panel,
  Chip,
  Heatmap,
  MINI_TABLE_CLS,
  MINI_TH,
  MINI_TH_NUM,
  MINI_TD,
  MINI_TD_NUM,
  MINI_ROW_BORDER,
  toneColorNumber,
} from "@/components/chartist/common/MockupPrimitives";
import { TickerName } from "@/components/shared/TickerName";
import {
  FLOW_SUMMARY,
  FLOW_FOREIGN_TOP,
  FLOW_INSTITUTION_TOP,
  FLOW_SECTOR_HEATMAP,
} from "@/lib/chartist/mockData";

export function FlowView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "수급 대시보드"]} />
      <PageHeader
        title="수급 대시보드"
        meta="외국인 · 기관 · 프로그램 · 연기금 · 개인 · 실시간"
      />
      <SummaryRow cells={FLOW_SUMMARY} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3">
        <Panel title="외국인 순매수 Top 10" subtitle="억원 · 5일 누적" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>#</th>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH}>Sector</th>
                <th className={MINI_TH_NUM}>당일</th>
                <th className={MINI_TH_NUM}>5D</th>
                <th className={MINI_TH_NUM}>20D</th>
                <th className={MINI_TH_NUM}>연속</th>
                <th className={MINI_TH_NUM}>가격%</th>
              </tr>
            </thead>
            <tbody>
              {FLOW_FOREIGN_TOP.map((r) => (
                <tr key={r.name} style={MINI_ROW_BORDER}>
                  <td className={`${MINI_TD} mono text-[10.5px]`}>
                    {String(r.rank).padStart(2, "0")}
                  </td>
                  <td className={MINI_TD}>
                    <TickerName symbol="" name={r.name} sector={r.sector} />
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone="accent">{r.sector}</Chip>
                  </td>
                  <td className={MINI_TD_NUM} style={{ color: "var(--pos)" }}>
                    +{r.d1}
                  </td>
                  <td className={MINI_TD_NUM} style={{ color: "var(--pos)" }}>
                    +{r.d5.toLocaleString()}
                  </td>
                  <td className={MINI_TD_NUM} style={{ color: "var(--pos)" }}>
                    +{r.d20.toLocaleString()}
                  </td>
                  <td className={MINI_TD_NUM}>{r.streak}</td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: toneColorNumber(r.pct) }}
                  >
                    {r.pct > 0 ? "+" : ""}
                    {r.pct.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="기관 순매수 Top 10" subtitle="투신+사모+연기금" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH_NUM}>투신</th>
                <th className={MINI_TH_NUM}>사모</th>
                <th className={MINI_TH_NUM}>연기금</th>
                <th className={MINI_TH_NUM}>합계</th>
              </tr>
            </thead>
            <tbody>
              {FLOW_INSTITUTION_TOP.map((r) => (
                <tr key={r.name} style={MINI_ROW_BORDER}>
                  <td className={MINI_TD}>
                    <TickerName symbol="" name={r.name} />
                  </td>
                  <td className={MINI_TD_NUM} style={{ color: "var(--pos)" }}>
                    +{r.tusin}
                  </td>
                  <td className={MINI_TD_NUM} style={{ color: "var(--pos)" }}>
                    +{r.samo}
                  </td>
                  <td className={MINI_TD_NUM} style={{ color: "var(--pos)" }}>
                    +{r.pension}
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: "var(--pos)", fontWeight: 600 }}
                  >
                    +{r.total}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>

      <Panel title="섹터별 외인 수급 Heatmap" subtitle="1D / 5D / 20D · 억원">
        <Heatmap
          headers={["Sector", "1D", "5D", "20D"]}
          rows={FLOW_SECTOR_HEATMAP}
        />
      </Panel>
    </div>
  );
}
