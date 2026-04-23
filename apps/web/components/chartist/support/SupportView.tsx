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
import type { SupportResponse, SupportRow } from "@/types/chartist";

function stateChip(state: string) {
  if (state === "AT_S") return { label: "AT SUPPORT", tone: "pos" as const };
  if (state === "AT_R") return { label: "AT RESISTANCE", tone: "neg" as const };
  return { label: "MID RANGE", tone: "neutral" as const };
}

function SRTable({ rows, show = "all" }: { rows: SupportRow[]; show?: "all" | "state" }) {
  return (
    <table className={MINI_TABLE_CLS}>
      <thead>
        <tr>
          <th className={MINI_TH}>Ticker</th>
          <th className={MINI_TH_NUM}>Price</th>
          <th className={MINI_TH_NUM}>Support</th>
          <th className={MINI_TH_NUM}>Dist S%</th>
          <th className={MINI_TH_NUM}>Resistance</th>
          <th className={MINI_TH_NUM}>Dist R%</th>
          <th className={MINI_TH_NUM}>Levels</th>
          {show === "all" && <th className={MINI_TH}>State</th>}
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr>
            <td
              colSpan={show === "all" ? 8 : 7}
              className={MINI_TD}
              style={{ textAlign: "center", color: "var(--fg-muted)" }}
            >
              해당 분류의 종목이 없습니다.
            </td>
          </tr>
        )}
        {rows.map((r) => {
          const st = stateChip(r.state);
          return (
            <tr key={r.symbol} style={MINI_ROW_BORDER}>
              <td className={MINI_TD}>
                <TickerName symbol={r.symbol} name={r.name} sector={r.sector} />
              </td>
              <td className={MINI_TD_NUM}>{r.close.toLocaleString()}</td>
              <td className={MINI_TD_NUM}>
                {r.nearest_support !== null ? r.nearest_support.toLocaleString() : "—"}
              </td>
              <td
                className={MINI_TD_NUM}
                style={{
                  color:
                    r.dist_support_pct !== null
                      ? r.dist_support_pct < 0
                        ? "var(--pos)"
                        : "var(--neg)"
                      : "var(--neutral)",
                }}
              >
                {r.dist_support_pct !== null
                  ? `${r.dist_support_pct > 0 ? "+" : ""}${r.dist_support_pct.toFixed(2)}%`
                  : "—"}
              </td>
              <td className={MINI_TD_NUM}>
                {r.nearest_resistance !== null
                  ? r.nearest_resistance.toLocaleString()
                  : "—"}
              </td>
              <td
                className={MINI_TD_NUM}
                style={{
                  color:
                    r.dist_resistance_pct !== null
                      ? r.dist_resistance_pct > 0
                        ? "var(--pos)"
                        : "var(--neg)"
                      : "var(--neutral)",
                }}
              >
                {r.dist_resistance_pct !== null
                  ? `${r.dist_resistance_pct > 0 ? "+" : ""}${r.dist_resistance_pct.toFixed(2)}%`
                  : "—"}
              </td>
              <td className={MINI_TD_NUM}>{r.levels.length}</td>
              {show === "all" && (
                <td className={MINI_TD}>
                  <Chip tone={st.tone}>{st.label}</Chip>
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export function SupportView({ data }: { data: SupportResponse }) {
  const s = data.summary ?? {};
  const cells = [
    { label: "At Support", value: String(s.at_support ?? 0), delta: "매수 검토", tone: "pos" as const },
    { label: "At Resistance", value: String(s.at_resistance ?? 0), delta: "돌파/이탈 주시", tone: "neg" as const },
    { label: "Mid Range", value: String(s.mid ?? 0), delta: "관망", tone: "neutral" as const },
    { label: "Total", value: String(data.count), delta: `종목 ${data.universe_size}`, tone: "neutral" as const },
    { label: "As-of", value: data.as_of, delta: "pivot + 장기 S/R", tone: "neutral" as const },
  ];

  const atS = data.rows.filter((r) => r.state === "AT_S");
  const atR = data.rows.filter((r) => r.state === "AT_R");
  const mid = data.rows.filter((r) => r.state === "MID");

  return (
    <div>
      <Breadcrumb trail={["Chartist", "지지/저항 자동감지"]} />
      <PageHeader
        title="지지/저항 자동감지"
        meta="Floor Pivot (전일 OHLC) + 장기 고점/저점 (5% 중복 제거)"
      />
      <SummaryRow cells={cells} />

      <Panel
        title="At Support"
        subtitle={`지지선 근처 (±1.5%) · ${atS.length}건`}
        bodyPad={false}
      >
        <SRTable rows={atS.slice(0, 50)} show="state" />
      </Panel>

      <Panel
        title="At Resistance"
        subtitle={`저항선 근처 (±1.5%) · ${atR.length}건`}
        bodyPad={false}
      >
        <SRTable rows={atR.slice(0, 50)} show="state" />
      </Panel>

      <Panel
        title="중립 구간 (상위 N)"
        subtitle={`가장 가까운 S/R 까지의 거리 기준 — ${mid.length}건`}
        bodyPad={false}
      >
        <SRTable rows={mid.slice(0, 40)} show="state" />
      </Panel>
    </div>
  );
}
