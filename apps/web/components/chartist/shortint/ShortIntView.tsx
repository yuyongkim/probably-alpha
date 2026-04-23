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
  toneColorNumber,
} from "@/components/chartist/common/MockupPrimitives";
import { TickerName } from "@/components/shared/TickerName";
import type {
  ShortIntResponse,
  ShortIntRow,
  SqueezeRow,
  SectorShort,
} from "@/types/chartist";

type ChipTone = "pos" | "neg" | "amber" | "neutral" | "accent";

function mapStatus(s: string): ChipTone {
  if (s === "과열") return "neg";
  if (s === "주의") return "amber";
  return "neutral";
}

function mapRisk(r: string): ChipTone {
  if (r === "High") return "pos";
  if (r === "Med") return "amber";
  return "neutral";
}

function fmtSigned(v: number, digits = 2): string {
  const s = v.toFixed(digits);
  return v > 0 ? `+${s}` : s;
}

export function ShortIntView({ data }: { data: ShortIntResponse }) {
  const top = data.overheated[0];
  const hottest = data.sector_overheat[0];

  const summary = [
    {
      label: "과열 종목",
      value: `${data.overheated.length}`,
      delta: "proxy ≥ 60",
      tone: "neg" as const,
    },
    {
      label: "숏스퀴즈",
      value: `${data.squeeze.length}`,
      delta: "candidates",
      tone: "pos" as const,
    },
    {
      label: "Top 과열",
      value: top ? top.name : "–",
      delta: top ? `${fmtSigned(top.pct_20d)}% / vol ${top.vol_ratio_20.toFixed(2)}×` : "–",
      tone: "neg" as const,
    },
    {
      label: "과열 섹터",
      value: hottest ? hottest.name : "–",
      delta: hottest ? `mean proxy ${hottest.mean_proxy_pct.toFixed(1)}` : "–",
      tone: "amber" as const,
    },
    {
      label: "as-of",
      value: data.as_of,
      delta: "EOD",
      tone: "neutral" as const,
    },
    {
      label: "Source",
      value: "proxy",
      delta: "panel-derived",
      tone: "neutral" as const,
    },
  ];

  return (
    <div>
      <Breadcrumb trail={["Chartist", "공매도 / 대차"]} />
      <PageHeader
        title="공매도 / 대차잔고"
        meta="프록시 기반 — 공매도 과열 / 숏스퀴즈 후보 · KRX 원천 연결 예정"
        asOf={data.as_of}
      />
      <SummaryRow cells={summary} />

      <div
        style={{
          background: "var(--surface-soft)",
          border: "1px solid var(--border)",
          borderRadius: 6,
          padding: "8px 12px",
          fontSize: 11,
          color: "var(--fg-muted)",
          marginBottom: 12,
        }}
      >
        <strong style={{ color: "var(--accent)" }}>NOTICE</strong> · {data.notice}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3">
        <Panel title="공매도 과열 후보" subtitle="20D 가격 하락 + 거래량 급증" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>#</th>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH}>Sector</th>
                <th className={MINI_TH_NUM}>5D%</th>
                <th className={MINI_TH_NUM}>20D%</th>
                <th className={MINI_TH_NUM}>Vol ×</th>
                <th className={MINI_TH_NUM}>Proxy</th>
                <th className={MINI_TH}>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.overheated.map((r: ShortIntRow) => (
                <tr key={r.symbol} style={MINI_ROW_BORDER}>
                  <td className={`${MINI_TD} mono text-[10.5px]`}>
                    {String(r.rank).padStart(2, "0")}
                  </td>
                  <td className={MINI_TD}>
                    <TickerName symbol={r.symbol} name={r.name} sector={r.sector} />
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone="accent">{r.sector}</Chip>
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: toneColorNumber(r.pct_5d) }}
                  >
                    {fmtSigned(r.pct_5d)}
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: toneColorNumber(r.pct_20d) }}
                  >
                    {fmtSigned(r.pct_20d)}
                  </td>
                  <td className={MINI_TD_NUM}>{r.vol_ratio_20.toFixed(2)}</td>
                  <td className={MINI_TD_NUM}>{r.short_proxy_pct.toFixed(1)}</td>
                  <td className={MINI_TD}>
                    <Chip tone={mapStatus(r.status)}>{r.status}</Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="숏스퀴즈 후보" subtitle="바닥 다지기 + 5D 고점 돌파" bodyPad={false}>
          <table className={MINI_TABLE_CLS}>
            <thead>
              <tr>
                <th className={MINI_TH}>#</th>
                <th className={MINI_TH}>Ticker</th>
                <th className={MINI_TH_NUM}>5D%</th>
                <th className={MINI_TH_NUM}>20D%</th>
                <th className={MINI_TH_NUM}>Vol ×</th>
                <th className={MINI_TH}>Trigger</th>
                <th className={MINI_TH}>Risk</th>
              </tr>
            </thead>
            <tbody>
              {data.squeeze.length === 0 && (
                <tr>
                  <td colSpan={7} className={MINI_TD} style={{ textAlign: "center", color: "var(--fg-muted)" }}>
                    현재 조건을 만족하는 후보가 없습니다.
                  </td>
                </tr>
              )}
              {data.squeeze.map((r: SqueezeRow) => (
                <tr key={r.symbol} style={MINI_ROW_BORDER}>
                  <td className={`${MINI_TD} mono text-[10.5px]`}>
                    {String(r.rank).padStart(2, "0")}
                  </td>
                  <td className={MINI_TD}>
                    <TickerName symbol={r.symbol} name={r.name} sector={r.sector} />
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: toneColorNumber(r.pct_5d) }}
                  >
                    {fmtSigned(r.pct_5d)}
                  </td>
                  <td
                    className={MINI_TD_NUM}
                    style={{ color: toneColorNumber(r.pct_20d) }}
                  >
                    {fmtSigned(r.pct_20d)}
                  </td>
                  <td className={MINI_TD_NUM}>{r.vol_ratio_5.toFixed(2)}</td>
                  <td className={MINI_TD}>
                    <Chip tone="amber">{r.trigger}</Chip>
                  </td>
                  <td className={MINI_TD}>
                    <Chip tone={mapRisk(r.risk)}>{r.risk}</Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>

      <Panel title="섹터별 공매도 과열 강도" subtitle="평균 proxy score · 과열 종목 수" bodyPad={false}>
        <table className={MINI_TABLE_CLS}>
          <thead>
            <tr>
              <th className={MINI_TH}>Sector</th>
              <th className={MINI_TH_NUM}>Members</th>
              <th className={MINI_TH_NUM}>Mean Proxy</th>
              <th className={MINI_TH_NUM}>과열 Count</th>
            </tr>
          </thead>
          <tbody>
            {data.sector_overheat.map((s: SectorShort) => (
              <tr key={s.name} style={MINI_ROW_BORDER}>
                <td className={MINI_TD}>{s.name}</td>
                <td className={MINI_TD_NUM}>{s.members}</td>
                <td className={MINI_TD_NUM}>{s.mean_proxy_pct.toFixed(1)}</td>
                <td className={MINI_TD_NUM}>{s.overheated}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
