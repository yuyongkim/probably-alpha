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
import type { CandlestickResponse } from "@/types/chartist";

export function CandlestickView({ data }: { data: CandlestickResponse }) {
  const s = data.summary ?? { bullish: 0, bearish: 0, neutral: 0 };
  const cells = [
    { label: "Bullish", value: String(s.bullish ?? 0), delta: "상승 반전+지속", tone: "pos" as const },
    { label: "Bearish", value: String(s.bearish ?? 0), delta: "하락 반전+지속", tone: "neg" as const },
    { label: "중립 / Doji", value: String(s.neutral ?? 0), delta: "Indecision", tone: "neutral" as const },
    { label: "Total Hits", value: String(data.count), delta: `종목 ${data.universe_size}`, tone: "neutral" as const },
    { label: "As-of", value: data.as_of, delta: "EOD", tone: "neutral" as const },
  ];
  return (
    <div>
      <Breadcrumb trail={["Chartist", "캔들스틱"]} />
      <PageHeader
        title="캔들스틱 패턴 스캐너"
        meta="15+ 고전 패턴 · 과거 승률 + 평균 +5D 수익률 (직접 산출)"
      />
      <SummaryRow cells={cells} />

      <Panel
        title="오늘의 패턴 히트"
        subtitle={`종목 · 패턴 · 신뢰도 — ${data.count}건 (상위 ${Math.min(data.count, data.rows.length)})`}
        bodyPad={false}
      >
        <table className={MINI_TABLE_CLS}>
          <thead>
            <tr>
              <th className={MINI_TH}>Ticker</th>
              <th className={MINI_TH}>Pattern</th>
              <th className={MINI_TH}>Type</th>
              <th className={MINI_TH_NUM}>과거 승률</th>
              <th className={MINI_TH_NUM}>평균 +5D</th>
              <th className={MINI_TH_NUM}>Vol×</th>
              <th className={MINI_TH_NUM}>N</th>
              <th className={MINI_TH}>Confluence</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => (
              <tr key={r.symbol + r.pattern} style={MINI_ROW_BORDER}>
                <td className={MINI_TD}>
                  <TickerName symbol={r.symbol} name={r.name} sector={r.sector} />
                </td>
                <td className={MINI_TD}>
                  <Chip
                    tone={
                      r.tone === "pos" ? "pos" : r.tone === "neg" ? "neg" : "neutral"
                    }
                  >
                    {r.pattern_ko}
                  </Chip>
                </td>
                <td className={`${MINI_TD} text-[11px]`}>{r.type}</td>
                <td className={MINI_TD_NUM}>
                  {r.sample_n > 0 ? `${r.win_rate.toFixed(1)}%` : "—"}
                </td>
                <td
                  className={MINI_TD_NUM}
                  style={{
                    color:
                      r.avg_fwd_5d > 0
                        ? "var(--pos)"
                        : r.avg_fwd_5d < 0
                          ? "var(--neg)"
                          : "var(--neutral)",
                  }}
                >
                  {r.avg_fwd_5d > 0 ? "+" : ""}
                  {r.avg_fwd_5d.toFixed(2)}%
                </td>
                <td className={MINI_TD_NUM}>{r.vol_x.toFixed(1)}×</td>
                <td className={MINI_TD_NUM}>{r.sample_n}</td>
                <td className={MINI_TD}>
                  <Chip
                    tone={
                      r.tone === "pos"
                        ? "accent"
                        : r.tone === "neg"
                          ? "neg"
                          : "neutral"
                    }
                  >
                    {r.confluence}
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
