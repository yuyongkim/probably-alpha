// Value · Consensus — 실데이터 (fnguide snapshots 기반).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary, type DenseSummaryCell } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { EmptyState } from "@/components/shared/EmptyState";
import { fetchEnvelope } from "@/lib/api";
import type { ConsensusResponse } from "@/types/value";

async function load(): Promise<ConsensusResponse | null> {
  try {
    return await fetchEnvelope<ConsensusResponse>(
      "/api/v1/value/consensus?mode=summary",
      { revalidate: 600 },
    );
  } catch {
    return null;
  }
}

const PCT = (v: number | null | undefined) =>
  v == null ? "—" : `${(v * 100).toFixed(1)}%`;

const NUM = (v: number | null | undefined, digits = 0) =>
  v == null ? "—" : v.toLocaleString("ko-KR", { maximumFractionDigits: digits });

export default async function ValueConsensusPage() {
  const data = await load();
  const kpi = data?.kpi;
  const cells: DenseSummaryCell[] = kpi
    ? [
        { label: "컨센 유효", value: String(kpi.total) },
        { label: "Positive", value: String(kpi.positive), tone: "pos" },
        { label: "Neutral", value: String(kpi.neutral) },
        { label: "Negative", value: String(kpi.negative), tone: "neg" },
        { label: "EPS Rev ↑ (1wk)", value: String(kpi.eps_rev_up), tone: "pos" },
        { label: "EPS Rev ↓ (1wk)", value: String(kpi.eps_rev_down), tone: "neg" },
      ]
    : [];

  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "애널리스트 컨센서스", current: true }]}
        title="애널리스트 컨센서스"
        meta="Investment Opinion · Target Price · EPS Revision"
      />
      {data ? <DenseSummary cells={cells} /> : null}
      <Panel
        title="EPS Revision Top 30"
        muted="consensus_eps vs forward estimate"
        bodyPadding="p0"
      >
        {!data || !data.rows || data.rows.length === 0 ? (
          <EmptyState title="컨센 데이터 부족" note="fnguide 스냅샷이 더 필요합니다." />
        ) : (
          <table className="mini">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Sector</th>
                <th className="num">Close</th>
                <th>Opinion</th>
                <th className="num">Consensus EPS</th>
                <th className="num">Fwd EPS</th>
                <th className="num">EPS Rev</th>
                <th className="num">TP Upside</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.slice(0, 30).map((r) => (
                <tr key={r.symbol}>
                  <td>
                    <span className="ticker-name">{r.name || r.symbol}</span>
                    <span className="mono"> {r.symbol}</span>
                  </td>
                  <td>{r.sector ? <span className="chip accent">{r.sector}</span> : "—"}</td>
                  <td className="num">{NUM(r.close)}</td>
                  <td>
                    <span
                      className={`chip${r.sentiment === "positive" ? " pos" : r.sentiment === "negative" ? " neg" : ""}`}
                    >
                      {r.opinion || r.sentiment}
                    </span>
                  </td>
                  <td className="num">{NUM(r.consensus_eps)}</td>
                  <td className="num">{NUM(r.forward_eps_estimate)}</td>
                  <td
                    className="num"
                    style={{
                      color:
                        (r.eps_rev ?? 0) > 0
                          ? "var(--pos)"
                          : (r.eps_rev ?? 0) < 0
                            ? "var(--neg)"
                            : undefined,
                    }}
                  >
                    {PCT(r.eps_rev)}
                  </td>
                  <td
                    className="num"
                    style={{
                      color:
                        (r.tp_upside ?? 0) > 0
                          ? "var(--pos)"
                          : (r.tp_upside ?? 0) < 0
                            ? "var(--neg)"
                            : undefined,
                    }}
                  >
                    {PCT(r.tp_upside)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </>
  );
}
