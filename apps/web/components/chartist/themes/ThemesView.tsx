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
  THEMES_SUMMARY,
  THEMES_HEATMAP,
  THEMES_HBM_DRILLDOWN,
  THEMES_RANKS,
} from "@/lib/chartist/mockData";

export function ThemesView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "테마 로테이션"]} />
      <PageHeader
        title="테마 로테이션"
        meta="20 THEMES · SECTOR와 별개 · 한국 시장 특화"
      />
      <SummaryRow cells={THEMES_SUMMARY} />

      <Panel
        title="20 테마 × 5 기간 Heatmap"
        subtitle="1D / 1W / 1M / 3M / YTD"
      >
        <Heatmap
          headers={["Theme", "1D", "1W", "1M", "3M", "YTD"]}
          rows={THEMES_HEATMAP}
        />
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Panel title="HBM 테마 구성 종목" subtitle="주도 테마 드릴다운" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH_NUM}>비중</th>
                <th className={MINI_TH_NUM}>1D</th>
                <th className={MINI_TH_NUM}>1M</th>
                <th className={MINI_TH_NUM}>YTD</th>
              </tr>
            </thead>
            <tbody>
              {THEMES_HBM_DRILLDOWN.map((r) => (
                <tr key={r.name} style={MINI_ROW_BORDER}>
                  <td className={MINI_TD}>
                    <TickerName symbol="" name={r.name} />
                  </td>
                  <td className={MINI_TD_NUM}>{r.weight}</td>
                  <td className={MINI_TD_NUM} style={{ color: toneColorNumber(r.d1) }}>
                    +{r.d1.toFixed(2)}
                  </td>
                  <td className={MINI_TD_NUM} style={{ color: toneColorNumber(r.m1) }}>
                    +{r.m1.toFixed(1)}
                  </td>
                  <td className={MINI_TD_NUM} style={{ color: toneColorNumber(r.ytd) }}>
                    +{r.ytd.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="테마 순위 변동 (4주)" subtitle="급부상 / 약세 전환" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>Theme</th>
                <th className={MINI_TH_NUM}>4w</th>
                <th className={MINI_TH_NUM}>2w</th>
                <th className={MINI_TH_NUM}>1w</th>
                <th className={MINI_TH_NUM}>now</th>
                <th className={MINI_TH}>Trend</th>
              </tr>
            </thead>
            <tbody>
              {THEMES_RANKS.map((r) => (
                <tr key={r.name} style={MINI_ROW_BORDER}>
                  <td className={MINI_TD}>{r.name}</td>
                  <td className={MINI_TD_NUM}>{r.w4}</td>
                  <td className={MINI_TD_NUM}>{r.w2}</td>
                  <td className={MINI_TD_NUM}>{r.w1}</td>
                  <td className={MINI_TD_NUM} style={{ fontWeight: 600 }}>
                    {r.now}
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone={r.tone === "pos" ? "pos" : r.tone === "neg" ? "neg" : "neutral"}>
                      {r.trend}
                    </Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>
    </div>
  );
}
