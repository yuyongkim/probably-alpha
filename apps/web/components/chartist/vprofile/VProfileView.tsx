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
import type { VProfileResponse, VProfileRow } from "@/types/chartist";

function positionChip(pos: string) {
  switch (pos) {
    case "ABOVE_VAH":
      return { label: "Above VAH", tone: "pos" as const };
    case "BELOW_VAL":
      return { label: "Below VAL", tone: "neg" as const };
    case "NEAR_POC":
      return { label: "Near POC", tone: "amber" as const };
    default:
      return { label: "Inside VA", tone: "neutral" as const };
  }
}

function VPTable({ rows }: { rows: VProfileRow[] }) {
  return (
    <table className={MINI_TABLE_CLS}>
      <thead>
        <tr>
          <th className={MINI_TH}>Ticker</th>
          <th className={MINI_TH_NUM}>Price</th>
          <th className={MINI_TH_NUM}>POC</th>
          <th className={MINI_TH_NUM}>VAH</th>
          <th className={MINI_TH_NUM}>VAL</th>
          <th className={MINI_TH_NUM}>POC % dist</th>
          <th className={MINI_TH}>Position</th>
          <th className={MINI_TH}>Signal</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td
              colSpan={8}
              className={MINI_TD}
              style={{ textAlign: "center", color: "var(--fg-muted)" }}
            >
              해당 분류의 종목이 없습니다.
            </td>
          </tr>
        )}
        {rows.map((r) => {
          const p = positionChip(r.position);
          return (
            <tr key={r.symbol} style={MINI_ROW_BORDER}>
              <td className={MINI_TD}>
                <TickerName symbol={r.symbol} name={r.name} sector={r.sector} />
              </td>
              <td className={MINI_TD_NUM}>{r.close.toLocaleString()}</td>
              <td className={MINI_TD_NUM}>{r.poc.toLocaleString()}</td>
              <td className={MINI_TD_NUM}>{r.vah.toLocaleString()}</td>
              <td className={MINI_TD_NUM}>{r.val.toLocaleString()}</td>
              <td
                className={MINI_TD_NUM}
                style={{
                  color: r.price_to_poc_pct > 0 ? "var(--pos)" : "var(--neg)",
                }}
              >
                {r.price_to_poc_pct > 0 ? "+" : ""}
                {r.price_to_poc_pct.toFixed(2)}%
              </td>
              <td className={MINI_TD}>
                <Chip tone={p.tone}>{p.label}</Chip>
              </td>
              <td className={MINI_TD}>
                <Chip
                  tone={
                    r.tone === "pos" ? "pos" : r.tone === "neg" ? "neg" : "amber"
                  }
                >
                  {r.signal}
                </Chip>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export function VProfileView({ data }: { data: VProfileResponse }) {
  const s = data.summary ?? {};
  const cells = [
    { label: "Breakout (>VAH)", value: String(s.above_vah ?? 0), delta: "밸류 에리어 상향 돌파", tone: "pos" as const },
    { label: "Near POC", value: String(s.near_poc ?? 0), delta: "결정점 근접 (S↔R)", tone: "amber" as const },
    { label: "Inside VA", value: String(s.inside_va ?? 0), delta: "value area 내부", tone: "neutral" as const },
    { label: "Breakdown (<VAL)", value: String(s.below_val ?? 0), delta: "밸류 에리어 이탈", tone: "neg" as const },
    { label: "Total", value: String(data.count), delta: `종목 ${data.universe_size}`, tone: "neutral" as const },
    { label: "As-of", value: data.as_of, delta: "60D VPVR", tone: "neutral" as const },
  ];

  const aboveVah = data.rows.filter((r) => r.position === "ABOVE_VAH");
  const nearPoc = data.rows.filter((r) => r.position === "NEAR_POC");
  const belowVal = data.rows.filter((r) => r.position === "BELOW_VAL");

  return (
    <div>
      <Breadcrumb trail={["Chartist", "Volume Profile"]} />
      <PageHeader
        title="Volume Profile (VPVR)"
        meta="POC · VAH · VAL · 60D 분포 기반 지지/저항"
      />
      <SummaryRow cells={cells} />

      <Panel
        title="Breakout above VAH"
        subtitle={`value area 위 돌파 — ${aboveVah.length}건`}
        bodyPad={false}
      >
        <VPTable rows={aboveVah.slice(0, 40)} />
      </Panel>

      <Panel
        title="POC 근접 (±1%)"
        subtitle={`가장 거래 많이 된 가격대 — ${nearPoc.length}건`}
        bodyPad={false}
      >
        <VPTable rows={nearPoc.slice(0, 40)} />
      </Panel>

      <Panel
        title="Breakdown below VAL"
        subtitle={`value area 아래 이탈 — ${belowVal.length}건`}
        bodyPad={false}
      >
        <VPTable rows={belowVal.slice(0, 40)} />
      </Panel>
    </div>
  );
}
