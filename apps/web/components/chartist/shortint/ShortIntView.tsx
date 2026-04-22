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
import {
  SHORT_SUMMARY,
  SHORT_OVERHEATED,
  SHORT_SQUEEZE,
} from "@/lib/chartist/mockData";

type ChipTone = "pos" | "neg" | "amber" | "neutral";

function mapTone(t: string): ChipTone {
  if (t === "neg") return "neg";
  if (t === "pos") return "pos";
  if (t === "amber") return "amber";
  return "neutral";
}

export function ShortIntView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "공매도 / 대차"]} />
      <PageHeader
        title="공매도 / 대차잔고"
        meta="공매도 과열 · 대차증감 · 숏스퀴즈 후보"
      />
      <SummaryRow cells={SHORT_SUMMARY} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3">
        <Panel title="공매도 과열 종목" subtitle="경보 발동 / 주의" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH}>Sector</th>
                <th className={MINI_TH_NUM}>공매도%</th>
                <th className={MINI_TH_NUM}>대차잔고</th>
                <th className={MINI_TH_NUM}>증감 1W</th>
                <th className={MINI_TH}>Status</th>
              </tr>
            </thead>
            <tbody>
              {SHORT_OVERHEATED.map((r) => (
                <tr key={r.name} style={MINI_ROW_BORDER}>
                  <td className={MINI_TD}>
                    <TickerName symbol="" name={r.name} sector={r.sector} />
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone="accent">{r.sector}</Chip>
                  </td>
                  <td className={MINI_TD_NUM}>{r.pct.toFixed(1)}</td>
                  <td className={MINI_TD_NUM}>{r.balance}</td>
                  <td
                    className={MINI_TD_NUM}
                    style={{
                      color: r.delta.startsWith("−")
                        ? "var(--pos)"
                        : "var(--neg)",
                    }}
                  >
                    {r.delta}
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone={mapTone(r.tone)}>{r.status}</Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="숏스퀴즈 후보" subtitle="잔고 高 + 차트 돌파" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH_NUM}>공매도%</th>
                <th className={MINI_TH_NUM}>가격 5D</th>
                <th className={MINI_TH}>Trigger</th>
                <th className={MINI_TH}>Risk</th>
              </tr>
            </thead>
            <tbody>
              {SHORT_SQUEEZE.map((r) => (
                <tr key={r.name} style={MINI_ROW_BORDER}>
                  <td className={MINI_TD}>
                    <TickerName symbol="" name={r.name} />
                  </td>
                  <td className={MINI_TD_NUM}>{r.pct.toFixed(1)}</td>
                  <td className={MINI_TD_NUM} style={{ color: "var(--pos)" }}>
                    +{r.d5.toFixed(1)}%
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone="amber">{r.trigger}</Chip>
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone={r.risk === "High" ? "pos" : "neutral"}>
                      {r.risk}
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
