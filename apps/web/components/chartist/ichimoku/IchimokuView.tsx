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
import type { IchimokuResponse, IchimokuRow } from "@/types/chartist";

function IchiTable({ rows }: { rows: IchimokuRow[] }) {
  return (
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
        {rows.length === 0 && (
          <tr>
            <td
              colSpan={7}
              className={MINI_TD}
              style={{ textAlign: "center", color: "var(--fg-muted)" }}
            >
              해당 분류의 종목이 없습니다.
            </td>
          </tr>
        )}
        {rows.map((r) => (
          <tr key={r.symbol} style={MINI_ROW_BORDER}>
            <td className={MINI_TD}>
              <TickerName symbol={r.symbol} name={r.name} sector={r.sector} />
            </td>
            <td className={MINI_TD}>
              <Chip tone="accent">{r.sector}</Chip>
            </td>
            <td className={MINI_TD}>
              <Chip tone={r.tk_cross === "BULL" ? "pos" : r.tk_cross === "BEAR" ? "neg" : "neutral"}>
                {r.tk_cross}
              </Chip>
            </td>
            <td className={MINI_TD}>
              <Chip tone={r.vs_cloud === "ABOVE" ? "pos" : r.vs_cloud === "BELOW" ? "neg" : "amber"}>
                {r.vs_cloud}
              </Chip>
            </td>
            <td className={MINI_TD}>
              <Chip tone={r.chikou === "ABOVE" ? "pos" : r.chikou === "BELOW" ? "neg" : "neutral"}>
                {r.chikou}
              </Chip>
            </td>
            <td className={MINI_TD_NUM}>{r.cloud_thickness_pct.toFixed(1)}%</td>
            <td className={MINI_TD}>
              <Chip
                tone={
                  r.three_cross_bull
                    ? "pos"
                    : r.three_cross_bear
                      ? "neg"
                      : r.tone === "pos"
                        ? "pos"
                        : r.tone === "neg"
                          ? "neg"
                          : "neutral"
                }
              >
                {r.three_cross_bull
                  ? "3-cross BULL"
                  : r.three_cross_bear
                    ? "3-cross BEAR"
                    : r.vs_cloud}
              </Chip>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function IchimokuView({ data }: { data: IchimokuResponse }) {
  const s = data.summary ?? {};
  const cells = [
    { label: "3-cross Bull", value: String(s.three_bull ?? 0), delta: "완벽 Bullish Ichimoku", tone: "pos" as const },
    { label: "3-cross Bear", value: String(s.three_bear ?? 0), delta: "완벽 Bearish", tone: "neg" as const },
    { label: "Above Cloud", value: String(s.above ?? 0), delta: "구름 위", tone: "pos" as const },
    { label: "Below Cloud", value: String(s.below ?? 0), delta: "구름 아래", tone: "neg" as const },
    { label: "Inside Cloud", value: String(s.inside ?? 0), delta: "혼조", tone: "neutral" as const },
    { label: "TK Cross Bull (5d)", value: String(s.tk_bull ?? 0), delta: `TK Bear ${s.tk_bear ?? 0}`, tone: "pos" as const },
  ];

  const threeBull = data.rows.filter((r) => r.three_cross_bull);
  const threeBear = data.rows.filter((r) => r.three_cross_bear);
  const recentTK = data.rows.filter((r) => r.tk_cross !== "—");

  return (
    <div>
      <Breadcrumb trail={["Chartist", "Ichimoku Cloud"]} />
      <PageHeader
        title="Ichimoku Cloud 스크리너"
        meta="TENKAN(9) · KIJUN(26) · SENKOU(52) · CHIKOU(-26)"
      />
      <SummaryRow cells={cells} />

      <Panel
        title="완벽 Bullish Ichimoku (3-cross align)"
        subtitle={`Tenkan > Kijun · Price > Cloud · Chikou > Price — ${threeBull.length}건`}
        bodyPad={false}
      >
        <IchiTable rows={threeBull.slice(0, 50)} />
      </Panel>

      <Panel
        title="완벽 Bearish Ichimoku"
        subtitle={`Tenkan < Kijun · Price < Cloud · Chikou < Price — ${threeBear.length}건`}
        bodyPad={false}
      >
        <IchiTable rows={threeBear.slice(0, 30)} />
      </Panel>

      <Panel
        title="최근 5일 TK Cross 발생"
        subtitle={`Tenkan/Kijun 최근 5일 교차 — ${recentTK.length}건`}
        bodyPad={false}
      >
        <IchiTable rows={recentTK.slice(0, 40)} />
      </Panel>
    </div>
  );
}
