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
import type { FlowResponse, FlowRow, SectorFlow } from "@/types/chartist";

function fmtSigned(v: number, digits = 0): string {
  const s = v.toFixed(digits);
  return v > 0 ? `+${s}` : s;
}

function streakLabel(streak: number): string {
  if (!streak) return "–";
  const sign = streak > 0 ? "+" : "−";
  return `${sign}${Math.abs(streak)}d`;
}

function FlowTable({
  rows,
  leg,
}: {
  rows: FlowRow[];
  leg: "foreign" | "institution" | "individual";
}) {
  return (
    <table className={MINI_TABLE_CLS}>
      <thead>
        <tr>
          <th className={MINI_TH}>#</th>
          <th className={MINI_TH}>Ticker</th>
          <th className={MINI_TH}>Sector</th>
          <th className={MINI_TH_NUM}>당일 (억)</th>
          <th className={MINI_TH_NUM}>5D 누적 (억)</th>
          <th className={MINI_TH_NUM}>전체 누적 (억)</th>
          <th className={MINI_TH_NUM}>연속</th>
          <th className={MINI_TH_NUM}>5D 가격%</th>
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
              {leg} 흐름 데이터가 아직 수집되지 않았습니다.
            </td>
          </tr>
        )}
        {rows.map((r) => (
          <tr key={`${leg}-${r.symbol}`} style={MINI_ROW_BORDER}>
            <td className={`${MINI_TD} mono text-[10.5px]`}>
              {String(r.rank).padStart(2, "0")}
            </td>
            <td className={MINI_TD}>
              <TickerName symbol={r.symbol} name={r.name} sector={r.sector} />
            </td>
            <td className={MINI_TD}>
              <Chip tone="accent">{r.sector}</Chip>
            </td>
            <td className={MINI_TD_NUM} style={{ color: toneColorNumber(r.d1) }}>
              {fmtSigned(r.d1, 0)}
            </td>
            <td className={MINI_TD_NUM} style={{ color: toneColorNumber(r.d5) }}>
              {fmtSigned(r.d5, 0)}
            </td>
            <td
              className={MINI_TD_NUM}
              style={{ color: toneColorNumber(r.d20) }}
            >
              {fmtSigned(r.d20, 0)}
            </td>
            <td
              className={MINI_TD_NUM}
              style={{ color: toneColorNumber(r.streak) }}
            >
              {streakLabel(r.streak)}
            </td>
            <td
              className={MINI_TD_NUM}
              style={{ color: toneColorNumber(r.price_pct) }}
            >
              {fmtSigned(r.price_pct, 2)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SectorFlowTable({ rows }: { rows: SectorFlow[] }) {
  return (
    <table className={MINI_TABLE_CLS}>
      <thead>
        <tr>
          <th className={MINI_TH}>Sector</th>
          <th className={MINI_TH_NUM}>Members</th>
          <th className={MINI_TH_NUM}>1D (억)</th>
          <th className={MINI_TH_NUM}>5D (억)</th>
          <th className={MINI_TH_NUM}>20D (억)</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((s) => (
          <tr key={s.name} style={MINI_ROW_BORDER}>
            <td className={MINI_TD}>{s.name}</td>
            <td className={MINI_TD_NUM}>{s.members}</td>
            <td className={MINI_TD_NUM} style={{ color: toneColorNumber(s.d1) }}>
              {fmtSigned(s.d1)}
            </td>
            <td className={MINI_TD_NUM} style={{ color: toneColorNumber(s.d5) }}>
              {fmtSigned(s.d5)}
            </td>
            <td className={MINI_TD_NUM} style={{ color: toneColorNumber(s.d20) }}>
              {fmtSigned(s.d20)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function FlowView({ data }: { data: FlowResponse }) {
  const fTop1 = data.foreign_top[0];
  const iTop1 = data.institution_top[0];
  const sector1 = data.sector_foreign[0];
  const summary = [
    {
      label: "as-of",
      value: data.as_of,
      delta: `coverage ${data.covered}/${data.universe_size}`,
      tone: "neutral" as const,
    },
    {
      label: "외국인 Top",
      value: fTop1 ? fTop1.name : "–",
      delta: fTop1 ? `5D ${fmtSigned(fTop1.d5)}억` : "–",
      tone: (fTop1 && fTop1.d5 >= 0 ? "pos" : "neg") as "pos" | "neg",
    },
    {
      label: "기관 Top",
      value: iTop1 ? iTop1.name : "–",
      delta: iTop1 ? `5D ${fmtSigned(iTop1.d5)}억` : "–",
      tone: (iTop1 && iTop1.d5 >= 0 ? "pos" : "neg") as "pos" | "neg",
    },
    {
      label: "Top 섹터 (외인)",
      value: sector1 ? sector1.name : "–",
      delta: sector1 ? `${fmtSigned(sector1.d5)}억 · ${sector1.members}개` : "–",
      tone: (sector1 && sector1.d5 >= 0 ? "pos" : "neg") as "pos" | "neg",
    },
    {
      label: "Source",
      value: "fnguide",
      delta: "investor_trend (10D)",
      tone: "neutral" as const,
    },
    {
      label: "Universe",
      value: `${data.universe_size}`,
      delta: "KOSPI+KOSDAQ",
      tone: "neutral" as const,
    },
  ];

  return (
    <div>
      <Breadcrumb trail={["Chartist", "수급 대시보드"]} />
      <PageHeader
        title="수급 대시보드"
        meta="외국인 · 기관 · 개인 · 섹터별 외인 Heatmap · 5D 기준"
        asOf={data.as_of}
      />
      <SummaryRow cells={summary} />

      <div className="grid grid-cols-1 gap-3 mb-3">
        <Panel
          title={`외국인 순매수 Top ${data.foreign_top.length}`}
          subtitle="억원 · 5D 누적 · fnguide investor_trend"
          bodyPad={false}
        >
          <FlowTable rows={data.foreign_top} leg="foreign" />
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-3">
        <Panel
          title={`기관 순매수 Top ${data.institution_top.length}`}
          subtitle="5D 누적"
          bodyPad={false}
        >
          <FlowTable rows={data.institution_top} leg="institution" />
        </Panel>
        <Panel
          title={`개인 순매수 Top ${data.individual_top.length}`}
          subtitle="5D 누적 (역수급 관점)"
          bodyPad={false}
        >
          <FlowTable rows={data.individual_top} leg="individual" />
        </Panel>
      </div>

      <Panel
        title="섹터별 외인 수급"
        subtitle="1D / 5D / 20D · 억원 (equal-weighted)"
        bodyPad={false}
      >
        <SectorFlowTable rows={data.sector_foreign} />
      </Panel>
    </div>
  );
}
