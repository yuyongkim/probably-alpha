// Value · Dividend — fnguide 배당수익률 + NI-streak 귀족 (실데이터).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary, type DenseSummaryCell } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { EmptyState } from "@/components/shared/EmptyState";
import { fetchEnvelope } from "@/lib/api";
import type { DividendResponse } from "@/types/value";

async function load(): Promise<DividendResponse | null> {
  try {
    return await fetchEnvelope<DividendResponse>(
      "/api/v1/value/dividend?mode=summary",
      { revalidate: 1800 },
    );
  } catch {
    return null;
  }
}

const NUM = (v: number | null | undefined, digits = 2) =>
  v == null ? "—" : v.toFixed(digits);

export default async function ValueDividendPage() {
  const data = await load();
  const kpi = data?.kpi;

  const cells: DenseSummaryCell[] = kpi
    ? [
        { label: "DY > 0", value: String(kpi.with_yield) },
        { label: "DY ≥ 5%", value: String(kpi.yield_gt_5pct), tone: "pos" },
        { label: "Aristocrat (proxy)", value: String(kpi.aristocrats), tone: "pos" },
        { label: "Basis", value: "NI streak", tone: "amber" },
        { label: "Next step", value: "DPS history", delta: "pending" },
        { label: "Source", value: "fnguide" },
      ]
    : [];

  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "배당주 스크리너", current: true }]}
        title="배당주 스크리너"
        meta="시가배당률 · 배당 귀족 후보 (NI 연속 성장 proxy)"
      />
      {data ? <DenseSummary cells={cells} /> : null}

      <Panel
        title="시가배당률 Top 50"
        muted={kpi ? `${kpi.with_yield}종 중` : undefined}
        bodyPadding="p0"
      >
        {!data || data.rows.length === 0 ? (
          <EmptyState title="배당 데이터 없음" note="fnguide 스냅샷이 더 필요합니다." />
        ) : (
          <table className="mini">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Sector</th>
                <th className="num">DY %</th>
                <th className="num">PER</th>
                <th className="num">PBR</th>
                <th className="num">ROE %</th>
                <th className="num">NI Streak</th>
                <th>Aristocrat?</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.slice(0, 50).map((r) => (
                <tr key={r.symbol}>
                  <td>
                    <span className="ticker-name">{r.name || r.symbol}</span>
                    <span className="mono"> {r.symbol}</span>
                  </td>
                  <td>{r.sector ? <span className="chip accent">{r.sector}</span> : "—"}</td>
                  <td className="num" style={{ color: "var(--pos)" }}>
                    {NUM(r.dividend_yield)}
                  </td>
                  <td className="num">{NUM(r.per)}</td>
                  <td className="num">{NUM(r.pbr)}</td>
                  <td className="num">{NUM(r.roe, 1)}</td>
                  <td className="num">
                    {r.ni_growth_streak}/{r.reported_years}
                  </td>
                  <td>
                    {r.aristocrat ? (
                      <span className="chip pos">candidate</span>
                    ) : (
                      <span className="chip">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>

      {data?.aristocrats && data.aristocrats.length > 0 ? (
        <Panel title="Aristocrat 후보 (NI streak ≥ 3)" muted="proxy" bodyPadding="p0">
          <table className="mini">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Sector</th>
                <th className="num">DY %</th>
                <th className="num">Streak</th>
              </tr>
            </thead>
            <tbody>
              {data.aristocrats.map((r) => (
                <tr key={r.symbol}>
                  <td>
                    <span className="ticker-name">{r.name || r.symbol}</span>
                    <span className="mono"> {r.symbol}</span>
                  </td>
                  <td>{r.sector ? <span className="chip accent">{r.sector}</span> : "—"}</td>
                  <td className="num" style={{ color: "var(--pos)" }}>
                    {NUM(r.dividend_yield)}
                  </td>
                  <td className="num">{r.ni_growth_streak}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      ) : null}
    </>
  );
}
