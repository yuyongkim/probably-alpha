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
import { ICHIMOKU_SUMMARY, ICHIMOKU_ROWS } from "@/lib/chartist/mockData";

export function IchimokuView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "Ichimoku Cloud"]} />
      <PageHeader
        title="Ichimoku Cloud 스크리너"
        meta="TENKAN · KIJUN · SENKOU · 구름 위/아래/돌파"
      />
      <SummaryRow cells={ICHIMOKU_SUMMARY} />

      <Panel
        title="완벽 Bullish Ichimoku (3-cross align)"
        subtitle="Tenkan > Kijun, Price > Cloud, Chikou > Price"
        bodyPad={false}
      >
        <table className={MINI_TABLE_CLS}>
          <thead>
            <tr>
              <th className={MINI_TH}>Ticker</th>
              <th className={MINI_TH}>Sector</th>
              <th className={MINI_TH}>TK Cross</th>
              <th className={MINI_TH}>vs Cloud</th>
              <th className={MINI_TH}>Chikou</th>
              <th className={MINI_TH_NUM}>Cloud 두께</th>
              <th className={MINI_TH}>Status</th>
            </tr>
          </thead>
          <tbody>
            {ICHIMOKU_ROWS.map((r) => (
              <tr key={r.name} style={MINI_ROW_BORDER}>
                <td className={MINI_TD}>
                  <TickerName symbol="" name={r.name} sector={r.sector} />
                </td>
                <td className={MINI_TD}>
                  <Chip tone="accent">{r.sector}</Chip>
                </td>
                <td className={MINI_TD}>
                  <Chip tone="pos">{r.tk}</Chip>
                </td>
                <td className={MINI_TD}>
                  <Chip tone="pos">{r.vsc}</Chip>
                </td>
                <td className={MINI_TD}>
                  <Chip tone="pos">{r.ch}</Chip>
                </td>
                <td className={MINI_TD_NUM}>{r.thick.toFixed(1)}%</td>
                <td className={MINI_TD}>
                  <Chip
                    tone={
                      r.tone === "pos" ? "pos" : r.tone === "amber" ? "amber" : "neutral"
                    }
                  >
                    {r.status}
                  </Chip>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
