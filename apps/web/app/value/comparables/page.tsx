// Value · Comparables — 섹터별 PER/PBR 랭킹 + cheap outliers (실데이터).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary, type DenseSummaryCell } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { EmptyState } from "@/components/shared/EmptyState";
import { fetchEnvelope } from "@/lib/api";
import type { ComparablesResponse } from "@/types/value";

async function load(): Promise<ComparablesResponse | null> {
  try {
    return await fetchEnvelope<ComparablesResponse>(
      "/api/v1/value/comparables?mode=summary",
      { revalidate: 1800 },
    );
  } catch {
    return null;
  }
}

const NUM = (v: number | null | undefined, digits = 2) =>
  v == null ? "—" : v.toFixed(digits);

const PCT = (v: number | null | undefined, digits = 0) =>
  v == null ? "—" : `${(v * 100).toFixed(digits)}%`;

export default async function ValueComparablesPage() {
  const data = await load();
  const kpi = data?.kpi;

  const cells: DenseSummaryCell[] = kpi
    ? [
        { label: "랭킹 대상", value: String(kpi.ranked) },
        { label: "Cheap Outliers", value: String(kpi.outlier_cheap), tone: "pos" },
        { label: "섹터 커버리지", value: String(kpi.sectors_covered) },
        { label: "Basis", value: "PER + PBR %rank", tone: "amber" },
        { label: "Threshold", value: "P≤25%, ROE>5%" },
        { label: "Source", value: "fnguide" },
      ]
    : [];

  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "동종업계 비교", current: true }]}
        title="Comparables"
        meta="섹터별 PER/PBR 백분위 · Cheap outliers"
      />
      {data ? <DenseSummary cells={cells} /> : null}

      <Panel
        title="Cheap Outliers (PER & PBR 하위 25%, ROE > 5%)"
        muted={data?.outliers?.length ? `${data.outliers.length}종` : undefined}
        bodyPadding="p0"
      >
        {!data?.outliers || data.outliers.length === 0 ? (
          <EmptyState title="Outlier 없음" note="조건을 만족하는 종목이 없습니다." />
        ) : (
          <table className="mini">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Sector</th>
                <th className="num">PER</th>
                <th className="num">PER %rank</th>
                <th className="num">PBR</th>
                <th className="num">PBR %rank</th>
                <th className="num">ROE %</th>
                <th className="num">DY %</th>
              </tr>
            </thead>
            <tbody>
              {data.outliers.slice(0, 30).map((r) => (
                <tr key={r.symbol}>
                  <td>
                    <span className="ticker-name">{r.name || r.symbol}</span>
                    <span className="mono"> {r.symbol}</span>
                  </td>
                  <td>{r.sector ? <span className="chip accent">{r.sector}</span> : "—"}</td>
                  <td className="num">{NUM(r.per)}</td>
                  <td className="num" style={{ color: "var(--pos)" }}>
                    {PCT(r.per_rank_pct)}
                  </td>
                  <td className="num">{NUM(r.pbr)}</td>
                  <td className="num" style={{ color: "var(--pos)" }}>
                    {PCT(r.pbr_rank_pct)}
                  </td>
                  <td className="num">{NUM(r.roe, 1)}</td>
                  <td className="num">{NUM(r.dividend_yield, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>

      {data?.top_sectors && data.top_sectors.length > 0 ? (
        <Panel title="섹터 커버리지" muted="랭킹된 종목 수" bodyPadding="p0">
          <table className="mini">
            <thead>
              <tr>
                <th>Sector</th>
                <th className="num">Ranked</th>
              </tr>
            </thead>
            <tbody>
              {data.top_sectors.map((s) => (
                <tr key={s.sector}>
                  <td>
                    <span className="chip accent">{s.sector}</span>
                  </td>
                  <td className="num">{s.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      ) : null}
    </>
  );
}
