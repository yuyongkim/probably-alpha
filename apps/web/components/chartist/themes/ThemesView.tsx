import {
  Breadcrumb,
  PageHeader,
  SummaryRow,
  Panel,
  Chip,
  Heatmap,
  type HeatCellProps,
  MINI_TABLE_CLS,
  MINI_TH,
  MINI_TH_NUM,
  MINI_TD,
  MINI_TD_NUM,
  MINI_ROW_BORDER,
  toneColorNumber,
} from "@/components/chartist/common/MockupPrimitives";
import { TickerName } from "@/components/shared/TickerName";
import type { ThemesResponse, ThemeRow } from "@/types/chartist";

function heatBucket(pct: number): number {
  if (pct <= -3) return 1;
  if (pct <= -1) return 2;
  if (pct < 0) return 3;
  if (pct < 1) return 4;
  if (pct < 3) return 5;
  return 6;
}

function fmtSigned(v: number, digits = 2): string {
  const s = v.toFixed(digits);
  return v > 0 ? `+${s}` : s;
}

function heatCell(v: number, digits = 2): HeatCellProps {
  return { v: fmtSigned(v, digits), h: heatBucket(v) };
}

function trendTone(trend: string): "pos" | "neg" | "neutral" {
  if (trend === "↗") return "pos";
  if (trend === "↘") return "neg";
  return "neutral";
}

export function ThemesView({ data }: { data: ThemesResponse }) {
  const top1 = data.rows[0];
  const covered = data.rows.reduce((s, r) => s + r.covered, 0);
  const members = data.rows.reduce((s, r) => s + r.members, 0);

  const summary = [
    {
      label: "Themes",
      value: `${data.count}`,
      delta: "KR retail narratives",
      tone: "neutral" as const,
    },
    {
      label: "1-week Top",
      value: top1 ? top1.name : "–",
      delta: top1 ? `${fmtSigned(top1.w1)}% · rank #1` : "–",
      tone: (top1 && top1.w1 >= 0 ? "pos" : "neg") as "pos" | "neg",
    },
    {
      label: "Top 종목",
      value: top1?.top_member ?? "–",
      delta: top1?.bucket ?? "–",
      tone: "neutral" as const,
    },
    {
      label: "Universe",
      value: `${covered}/${members}`,
      delta: "covered members",
      tone: "neutral" as const,
    },
    {
      label: "as-of",
      value: data.as_of,
      delta: "EOD",
      tone: "neutral" as const,
    },
    {
      label: "Source",
      value: "themes.yml",
      delta: "equal-weighted",
      tone: "neutral" as const,
    },
  ];

  const heatmapRows = data.rows.map((r) => ({
    name: r.name,
    cells: [
      heatCell(r.d1),
      heatCell(r.w1),
      heatCell(r.m1),
      heatCell(r.m3),
      heatCell(r.ytd),
    ],
  }));

  // Drilldown: pick the leading theme (rank_now === 1) rather than hard-coded HBM.
  const lead = data.rows.find((r) => r.rank_now === 1) ?? data.rows[0];

  return (
    <div>
      <Breadcrumb trail={["Chartist", "테마 로테이션"]} />
      <PageHeader
        title="테마 로테이션"
        meta={`${data.count} 테마 · equal-weighted 수익률 · KOSPI/KOSDAQ`}
        asOf={data.as_of}
      />
      <SummaryRow cells={summary} />

      <Panel
        title={`${data.count} 테마 × 5 기간 Heatmap`}
        subtitle="1D / 1W / 1M / 3M / YTD (%)"
      >
        <Heatmap
          headers={["Theme", "1D", "1W", "1M", "3M", "YTD"]}
          rows={heatmapRows}
        />
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Panel
          title={`${lead?.name ?? "?"} 테마 구성 종목`}
          subtitle={`주도 테마 드릴다운 · covered ${lead?.covered}/${lead?.members}`}
          bodyPad={false}
        >
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH_NUM}>비중</th>
                <th className={MINI_TH_NUM}>1D</th>
                <th className={MINI_TH_NUM}>1W</th>
                <th className={MINI_TH_NUM}>1M</th>
                <th className={MINI_TH_NUM}>YTD</th>
              </tr>
            </thead>
            <tbody>
              {(lead?.constituents ?? []).map((m) => (
                <tr key={m.symbol} style={MINI_ROW_BORDER}>
                  <td className={MINI_TD}>
                    <TickerName symbol={m.symbol} name={m.name} sector={m.sector} />
                  </td>
                  <td className={MINI_TD_NUM}>
                    {(m.weight * 100).toFixed(1)}%
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: toneColorNumber(m.d1) }}
                  >
                    {fmtSigned(m.d1)}
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: toneColorNumber(m.w1) }}
                  >
                    {fmtSigned(m.w1)}
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: toneColorNumber(m.m1) }}
                  >
                    {fmtSigned(m.m1)}
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: toneColorNumber(m.ytd) }}
                  >
                    {fmtSigned(m.ytd)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="테마 순위 변동" subtitle="4w · 2w · 1w · now" bodyPad={false}>
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
              {data.rows.map((r: ThemeRow) => (
                <tr key={r.code} style={MINI_ROW_BORDER}>
                  <td className={MINI_TD}>{r.name}</td>
                  <td className={MINI_TD_NUM}>{r.rank_w4}</td>
                  <td className={MINI_TD_NUM}>{r.rank_w2}</td>
                  <td className={MINI_TD_NUM}>{r.rank_w1}</td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ fontWeight: 600 }}
                  >
                    {r.rank_now}
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone={trendTone(r.trend)}>
                      {r.trend} {r.delta_4w > 0 ? `+${r.delta_4w}` : r.delta_4w}
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
