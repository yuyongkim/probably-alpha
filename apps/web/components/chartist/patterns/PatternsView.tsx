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
import type { PatternsResponse, PatternRow } from "@/types/chartist";

function patternTone(p: string): "pos" | "accent" | "amber" | "neutral" {
  if (p === "VCP") return "accent";
  if (p === "Cup&Handle") return "pos";
  if (p === "Flat Base") return "amber";
  if (p === "Asc Triangle") return "pos";
  return "neutral";
}

function PatTable({ rows }: { rows: PatternRow[] }) {
  return (
    <table className={MINI_TABLE_CLS}>
      <thead>
        <tr>
          <th className={MINI_TH}>Ticker</th>
          <th className={MINI_TH}>Pattern</th>
          <th className={MINI_TH_NUM}>Stage</th>
          <th className={MINI_TH_NUM}>Score</th>
          <th className={MINI_TH_NUM}>%52w High</th>
          <th className={MINI_TH_NUM}>Depth %</th>
          <th className={MINI_TH_NUM}>Duration</th>
          <th className={MINI_TH}>Vol Dry-up</th>
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
              해당 패턴이 감지된 종목이 없습니다.
            </td>
          </tr>
        )}
        {rows.map((r) => (
          <tr key={r.symbol + r.pattern} style={MINI_ROW_BORDER}>
            <td className={MINI_TD}>
              <TickerName symbol={r.symbol} name={r.name} sector={r.sector} />
            </td>
            <td className={MINI_TD}>
              <Chip tone={patternTone(r.pattern)}>{r.pattern}</Chip>
            </td>
            <td className={MINI_TD_NUM}>{r.stage}</td>
            <td className={MINI_TD_NUM}>{r.score.toFixed(2)}</td>
            <td className={MINI_TD_NUM}>
              {(r.pct_of_52w_high * 100).toFixed(1)}%
            </td>
            <td className={MINI_TD_NUM}>{r.depth_pct.toFixed(1)}%</td>
            <td className={MINI_TD_NUM}>{r.duration_days}d</td>
            <td className={MINI_TD}>
              <Chip tone={r.volume_dry_up ? "pos" : "neutral"}>
                {r.volume_dry_up ? "DRY" : "—"}
              </Chip>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function PatternsView({ data }: { data: PatternsResponse }) {
  const s = data.summary ?? {};
  const cells = [
    { label: "VCP", value: String(s.VCP ?? 0), delta: "변동성 수축", tone: "pos" as const },
    { label: "Cup & Handle", value: String(s["Cup&Handle"] ?? 0), delta: "컵 + 손잡이", tone: "pos" as const },
    { label: "Flat Base", value: String(s["Flat Base"] ?? 0), delta: "20일+ 박스", tone: "pos" as const },
    { label: "Asc Triangle", value: String(s["Asc Triangle"] ?? 0), delta: "상승 삼각형", tone: "pos" as const },
    { label: "Stage 3+", value: String(s["stage3+"] ?? 0), delta: "돌파 임박", tone: "pos" as const },
    { label: "As-of", value: data.as_of, delta: "EOD", tone: "neutral" as const },
  ];

  const vcp = data.rows.filter((r) => r.pattern === "VCP");
  const cup = data.rows.filter((r) => r.pattern === "Cup&Handle");
  const flat = data.rows.filter((r) => r.pattern === "Flat Base");
  const asc = data.rows.filter((r) => r.pattern === "Asc Triangle");

  return (
    <div>
      <Breadcrumb trail={["Chartist", "VCP / Base 패턴"]} />
      <PageHeader
        title="VCP / Base 패턴 탐지"
        meta="Minervini VCP · Cup&Handle · Flat Base · Asc Triangle"
      />
      <SummaryRow cells={cells} />

      <Panel
        title="VCP (Volatility Contraction Pattern)"
        subtitle={`수축 단계별 — ${vcp.length}건`}
        bodyPad={false}
      >
        <PatTable rows={vcp.slice(0, 60)} />
      </Panel>

      <Panel
        title="Cup with Handle"
        subtitle={`쿠프 + 얕은 손잡이 · 거래량 건조 — ${cup.length}건`}
        bodyPad={false}
      >
        <PatTable rows={cup.slice(0, 60)} />
      </Panel>

      <Panel
        title="Flat Base"
        subtitle={`20일+ 박스 (range ≤ 15%) · 선행 상승 25%+ — ${flat.length}건`}
        bodyPad={false}
      >
        <PatTable rows={flat.slice(0, 40)} />
      </Panel>

      <Panel
        title="Ascending Triangle"
        subtitle={`평평한 고점 + 상승하는 저점 — ${asc.length}건`}
        bodyPad={false}
      >
        <PatTable rows={asc.slice(0, 40)} />
      </Panel>
    </div>
  );
}
