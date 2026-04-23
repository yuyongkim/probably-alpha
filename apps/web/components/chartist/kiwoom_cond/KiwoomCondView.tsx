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
  KiwoomCondResponse,
  KiwoomCondBucket,
  KiwoomCondHit,
} from "@/types/chartist";

function fmtSigned(v: number, digits = 2): string {
  const s = v.toFixed(digits);
  return v > 0 ? `+${s}` : s;
}

function HitTable({ rows, title }: { rows: KiwoomCondHit[]; title: string }) {
  return (
    <Panel
      title={title}
      subtitle={`${rows.length} 종목 · volume × pct_1d 정렬`}
      bodyPad={false}
    >
      <table className={MINI_TABLE_CLS}>
        <thead>
          <tr>
            <th className={MINI_TH}>Ticker</th>
            <th className={MINI_TH}>Sector</th>
            <th className={MINI_TH_NUM}>Close</th>
            <th className={MINI_TH_NUM}>1D%</th>
            <th className={MINI_TH_NUM}>Vol ×</th>
            <th className={MINI_TH}>Pass</th>
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
                조건을 충족한 종목이 없습니다.
              </td>
            </tr>
          )}
          {rows.map((h) => (
            <tr key={h.symbol} style={MINI_ROW_BORDER}>
              <td className={MINI_TD}>
                <TickerName symbol={h.symbol} name={h.name} sector={h.sector} />
              </td>
              <td className={MINI_TD}>
                <Chip tone="accent">{h.sector}</Chip>
              </td>
              <td className={MINI_TD_NUM}>{h.close.toLocaleString()}</td>
              <td
                className={MINI_TD_NUM}
                style={{ color: toneColorNumber(h.pct_1d) }}
              >
                {fmtSigned(h.pct_1d)}
              </td>
              <td className={MINI_TD_NUM}>{h.vol_ratio.toFixed(2)}</td>
              <td className={MINI_TD}>
                <Chip tone="pos">{h.reason}</Chip>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Panel>
  );
}

export function KiwoomCondView({ data }: { data: KiwoomCondResponse }) {
  const maxBucket = data.buckets.reduce(
    (acc, b) => (b.pass_count > acc.pass_count ? b : acc),
    data.buckets[0] ?? { id: "?", name: "–", pass_count: 0 } as KiwoomCondBucket,
  );

  const summary = [
    {
      label: "조건식",
      value: `${data.buckets.length}`,
      delta: "A..G",
      tone: "neutral" as const,
    },
    {
      label: "총 Pass",
      value: `${data.total_pass}`,
      delta: "모든 조건 합산",
      tone: "pos" as const,
    },
    {
      label: "최대 Pass",
      value: `${maxBucket.pass_count}`,
      delta: maxBucket.name,
      tone: "pos" as const,
    },
    {
      label: "4+ 교집합",
      value: `${data.intersection_4of7.length}`,
      delta: "매매 후보",
      tone: "pos" as const,
    },
    {
      label: "7/7 통과",
      value: `${data.intersection_all.length}`,
      delta: "Prime signal",
      tone: "amber" as const,
    },
    {
      label: "Universe",
      value: `${data.universe_size.toLocaleString()}`,
      delta: "KOSPI+KOSDAQ",
      tone: "neutral" as const,
    },
  ];

  return (
    <div>
      <Breadcrumb trail={["Chartist", "키움 조건식"]} />
      <PageHeader
        title="키움 조건식 7종"
        meta="MA 수렴/GC · 거래량 급증 · 유동성 필터 · QuantPlatform 이식"
        asOf={data.as_of}
      />
      <SummaryRow cells={summary} />

      <Panel
        title="조건식 현황"
        subtitle="A..G · 각 조건 통과 종목 수"
        bodyPad={false}
      >
        <table className={MINI_TABLE_CLS}>
          <thead>
            <tr>
              <th className={MINI_TH}>#</th>
              <th className={MINI_TH}>조건식</th>
              <th className={MINI_TH}>설명</th>
              <th className={MINI_TH_NUM}>Pass</th>
              <th className={MINI_TH}>Top 1</th>
            </tr>
          </thead>
          <tbody>
            {data.buckets.map((b) => (
              <tr key={b.id} style={MINI_ROW_BORDER}>
                <td className={`${MINI_TD} mono text-[10.5px]`}>{b.id}</td>
                <td className={MINI_TD}>{b.name}</td>
                <td className={MINI_TD} style={{ color: "var(--fg-muted)" }}>
                  {b.desc}
                </td>
                <td className={MINI_TD_NUM} style={{ fontWeight: 600 }}>
                  {b.pass_count.toLocaleString()}
                </td>
                <td className={MINI_TD}>
                  {b.top[0] ? (
                    <TickerName
                      symbol={b.top[0].symbol}
                      name={b.top[0].name}
                      sector={b.top[0].sector}
                    />
                  ) : (
                    <span style={{ color: "var(--fg-muted)" }}>–</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mt-3">
        <HitTable
          rows={data.intersection_4of7.slice(0, 20)}
          title={`4+/7 교집합 · ${data.intersection_4of7.length} 종목`}
        />
        <HitTable
          rows={data.intersection_all.slice(0, 20)}
          title={`7/7 만점 · ${data.intersection_all.length} 종목`}
        />
      </div>
    </div>
  );
}
