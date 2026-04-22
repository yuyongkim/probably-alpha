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
  DIVERGENCE_SUMMARY,
  DIVERGENCE_BULL,
  DIVERGENCE_BEAR,
} from "@/lib/chartist/mockData";

type Row = {
  name: string;
  ind: string;
  rsi: number;
  d5: number;
  str: string;
  tone: string;
};

function DivPanel({ title, subtitle, rows }: { title: string; subtitle: string; rows: Row[] }) {
  return (
    <Panel title={title} subtitle={subtitle} bodyPad={false}>
      <table className={MINI_TABLE_CLS}>
        <thead>
          <tr>
            <th className={MINI_TH}>Ticker</th>
            <th className={MINI_TH}>Indicator</th>
            <th className={MINI_TH_NUM}>RSI</th>
            <th className={MINI_TH_NUM}>5D 가격</th>
            <th className={MINI_TH}>Strength</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.name + r.ind} style={MINI_ROW_BORDER}>
              <td className={MINI_TD}>
                <TickerName symbol="" name={r.name} />
              </td>
              <td className={`${MINI_TD} text-[11px]`}>{r.ind}</td>
              <td className={MINI_TD_NUM}>{r.rsi.toFixed(1)}</td>
              <td
                className={MINI_TD_NUM}
                style={{
                  color: r.d5 > 0 ? "var(--pos)" : "var(--neg)",
                }}
              >
                {r.d5 > 0 ? "+" : ""}
                {r.d5.toFixed(1)}%
              </td>
              <td className={MINI_TD}>
                <Chip
                  tone={
                    r.tone === "pos" ? "pos" : r.tone === "neg" ? "neg" : "amber"
                  }
                >
                  {r.str}
                </Chip>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

export function DivergenceView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "Divergence Scanner"]} />
      <PageHeader
        title="Divergence Scanner"
        meta="RSI · MACD · OBV · BULLISH / BEARISH · HIDDEN"
      />
      <SummaryRow cells={DIVERGENCE_SUMMARY} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <DivPanel
          title="Bullish Divergence"
          subtitle="가격↓ 지표↑ · 반전 기대"
          rows={DIVERGENCE_BULL}
        />
        <DivPanel
          title="Bearish Divergence"
          subtitle="가격↑ 지표↓ · 조정 경고"
          rows={DIVERGENCE_BEAR}
        />
      </div>
    </div>
  );
}
