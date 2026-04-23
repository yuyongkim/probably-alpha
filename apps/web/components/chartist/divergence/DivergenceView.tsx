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
import type { DivergenceResponse, DivergenceRow } from "@/types/chartist";

function DivPanel({
  title,
  subtitle,
  rows,
}: {
  title: string;
  subtitle: string;
  rows: DivergenceRow[];
}) {
  return (
    <Panel title={title} subtitle={subtitle} bodyPad={false}>
      <table className={MINI_TABLE_CLS}>
        <thead>
          <tr>
            <th className={MINI_TH}>Ticker</th>
            <th className={MINI_TH}>Indicator</th>
            <th className={MINI_TH}>Kind</th>
            <th className={MINI_TH_NUM}>RSI</th>
            <th className={MINI_TH_NUM}>5D 가격</th>
            <th className={MINI_TH}>Strength</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td
                colSpan={6}
                className={MINI_TD}
                style={{ textAlign: "center", color: "var(--fg-muted)" }}
              >
                오늘은 해당 divergence 히트가 없습니다.
              </td>
            </tr>
          )}
          {rows.map((r) => (
            <tr key={r.symbol + r.indicator + r.kind} style={MINI_ROW_BORDER}>
              <td className={MINI_TD}>
                <TickerName symbol={r.symbol} name={r.name} sector={r.sector} />
              </td>
              <td className={`${MINI_TD} text-[11px]`}>{r.indicator}</td>
              <td className={MINI_TD}>
                <Chip tone={r.tone === "pos" ? "pos" : "neg"}>
                  {r.kind.startsWith("hidden") ? "Hidden " : ""}
                  {r.kind.includes("bullish") ? "Bull" : "Bear"}
                </Chip>
              </td>
              <td className={MINI_TD_NUM}>{r.rsi.toFixed(1)}</td>
              <td
                className={MINI_TD_NUM}
                style={{
                  color: r.d5_pct > 0 ? "var(--pos)" : "var(--neg)",
                }}
              >
                {r.d5_pct > 0 ? "+" : ""}
                {r.d5_pct.toFixed(1)}%
              </td>
              <td className={MINI_TD}>
                <Chip
                  tone={
                    r.strength_label === "STRONG"
                      ? r.tone === "pos"
                        ? "pos"
                        : "neg"
                      : "amber"
                  }
                >
                  {r.strength_label}
                </Chip>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

export function DivergenceView({ data }: { data: DivergenceResponse }) {
  const s = data.summary ?? {};
  const cells = [
    { label: "Bullish (regular)", value: String(s.bullish ?? 0), delta: "가격↓ 지표↑", tone: "pos" as const },
    { label: "Bearish (regular)", value: String(s.bearish ?? 0), delta: "가격↑ 지표↓", tone: "neg" as const },
    { label: "Hidden Bull", value: String(s.hidden_bullish ?? 0), delta: "continuation up", tone: "pos" as const },
    { label: "Hidden Bear", value: String(s.hidden_bearish ?? 0), delta: "continuation down", tone: "neg" as const },
    { label: "Total Hits", value: String(data.count), delta: `종목 ${data.universe_size}`, tone: "neutral" as const },
    { label: "As-of", value: data.as_of, delta: "EOD", tone: "neutral" as const },
  ];

  const bull = data.rows.filter((r) => r.kind === "bullish");
  const bear = data.rows.filter((r) => r.kind === "bearish");
  const hiddenBull = data.rows.filter((r) => r.kind === "hidden_bullish");
  const hiddenBear = data.rows.filter((r) => r.kind === "hidden_bearish");

  return (
    <div>
      <Breadcrumb trail={["Chartist", "Divergence Scanner"]} />
      <PageHeader
        title="Divergence Scanner"
        meta="RSI · MACD · OBV · REGULAR / HIDDEN · BULL / BEAR"
      />
      <SummaryRow cells={cells} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <DivPanel
          title="Regular Bullish"
          subtitle="가격↓ 지표↑ · 반전 기대"
          rows={bull.slice(0, 40)}
        />
        <DivPanel
          title="Regular Bearish"
          subtitle="가격↑ 지표↓ · 조정 경고"
          rows={bear.slice(0, 40)}
        />
        <DivPanel
          title="Hidden Bullish"
          subtitle="가격 higher-low, 지표 lower-low · 추세 지속 (상방)"
          rows={hiddenBull.slice(0, 40)}
        />
        <DivPanel
          title="Hidden Bearish"
          subtitle="가격 lower-high, 지표 higher-high · 추세 지속 (하방)"
          rows={hiddenBear.slice(0, 40)}
        />
      </div>
    </div>
  );
}
