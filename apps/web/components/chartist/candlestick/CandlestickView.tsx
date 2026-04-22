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
import { CANDLESTICK_SUMMARY, CANDLESTICK_HITS } from "@/lib/chartist/mockData";

export function CandlestickView() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "캔들스틱 57종"]} />
      <PageHeader
        title="캔들스틱 패턴 스캐너"
        meta="57 PATTERNS · KIS BACKTESTER 재료 · 신뢰도 + 평균 이후 수익률"
      />
      <SummaryRow cells={CANDLESTICK_SUMMARY} />

      <Panel title="오늘의 패턴 히트" subtitle="종목 · 패턴 · 신뢰도" bodyPad={false}>
        <table className={MINI_TABLE_CLS}>
          <thead>
            <tr>
              <th className={MINI_TH}>Ticker</th>
              <th className={MINI_TH}>Pattern</th>
              <th className={MINI_TH}>Type</th>
              <th className={MINI_TH_NUM}>과거 승률</th>
              <th className={MINI_TH_NUM}>평균 +5D</th>
              <th className={MINI_TH_NUM}>Vol×</th>
              <th className={MINI_TH}>Confluence</th>
            </tr>
          </thead>
          <tbody>
            {CANDLESTICK_HITS.map((r) => (
              <tr key={r.name + r.pattern} style={MINI_ROW_BORDER}>
                <td className={MINI_TD}>
                  <TickerName symbol="" name={r.name} />
                </td>
                <td className={MINI_TD}>
                  <Chip
                    tone={
                      r.tone === "pos" ? "pos" : r.tone === "neg" ? "neg" : "neutral"
                    }
                  >
                    {r.pattern}
                  </Chip>
                </td>
                <td className={`${MINI_TD} text-[11px]`}>{r.type}</td>
                <td className={MINI_TD_NUM}>
                  {r.wr !== null ? `${r.wr.toFixed(1)}%` : "—"}
                </td>
                <td
                  className={MINI_TD_NUM}
                  style={{
                    color:
                      r.avg5 > 0
                        ? "var(--pos)"
                        : r.avg5 < 0
                          ? "var(--neg)"
                          : "var(--neutral)",
                  }}
                >
                  {r.avg5 > 0 ? "+" : ""}
                  {r.avg5.toFixed(2)}%
                </td>
                <td className={MINI_TD_NUM}>{r.volx.toFixed(1)}×</td>
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
                    {r.cf}
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
