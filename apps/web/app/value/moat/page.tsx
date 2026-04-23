// Value · Moat — 10년 ROIC 평균/변동성 기반 실데이터.

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary, type DenseSummaryCell } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { EmptyState } from "@/components/shared/EmptyState";
import { fetchEnvelope } from "@/lib/api";
import type { MoatResponse } from "@/types/value";

async function load(): Promise<MoatResponse | null> {
  try {
    return await fetchEnvelope<MoatResponse>(
      "/api/v1/value/moat?mode=summary",
      { revalidate: 1800 },
    );
  } catch {
    return null;
  }
}

const PCT = (v: number | null | undefined, digits = 1) =>
  v == null ? "—" : `${(v * 100).toFixed(digits)}%`;

export default async function ValueMoatPage() {
  const data = await load();
  const kpi = data?.kpi;

  const cells: DenseSummaryCell[] = kpi
    ? [
        { label: "스캔 대상", value: String(kpi.total) },
        { label: "Wide Moat", value: String(kpi.wide), tone: "pos" },
        { label: "Narrow Moat", value: String(kpi.narrow), tone: "pos" },
        { label: "No Moat", value: String(kpi.none) },
        {
          label: "분류 기준",
          value: "ROIC 10y",
          delta: "≥15% μ, ≤5pp σ",
        },
        { label: "Source", value: "financials_pit" },
      ]
    : [];

  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "경제적 해자", current: true }]}
        title="경제적 해자 분석 (Moat)"
        meta="10년 ROIC 평균 & 변동성 · ROE consistency · Morningstar-style"
      />
      {data ? <DenseSummary cells={cells} /> : null}
      <Panel
        title="Wide / Narrow Moat 종목"
        muted="ROIC 평균 ≥ 10%, 변동성 ≤ 8pp"
        bodyPadding="p0"
      >
        {!data || data.rows.length === 0 ? (
          <EmptyState
            title="Moat 결과 없음"
            note="annual 재무 데이터가 부족합니다 (≥5y 필요)."
          />
        ) : (
          <table className="mini">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Sector</th>
                <th>Moat</th>
                <th className="num">ROIC μ 10y</th>
                <th className="num">ROIC σ</th>
                <th className="num">ROE&gt;10% Yrs</th>
                <th className="num">Rev CAGR</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.slice(0, 80).map((r) => (
                <tr key={r.symbol}>
                  <td>
                    <span className="ticker-name">{r.name || r.symbol}</span>
                    <span className="mono"> {r.symbol}</span>
                  </td>
                  <td>
                    {r.sector ? (
                      <span className="chip accent">{r.sector}</span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>
                    <span
                      className={`chip${r.moat === "wide" ? " pos" : r.moat === "narrow" ? " amber" : ""}`}
                    >
                      {r.moat.toUpperCase()}
                    </span>
                  </td>
                  <td className="num">{PCT(r.roic_10y_mean)}</td>
                  <td className="num">{PCT(r.roic_10y_std, 2)}</td>
                  <td className="num">
                    {r.roe_years_above_10pct}/{r.years_used}
                  </td>
                  <td className="num">{PCT(r.revenue_cagr)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </>
  );
}
