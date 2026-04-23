// Value · Segment — SOTP/Conglomerate 할인 (proxy 실데이터).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary, type DenseSummaryCell } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { EmptyState } from "@/components/shared/EmptyState";
import { fetchEnvelope } from "@/lib/api";
import type { SegmentResponse } from "@/types/value";

async function load(): Promise<SegmentResponse | null> {
  try {
    return await fetchEnvelope<SegmentResponse>(
      "/api/v1/value/segment",
      { revalidate: 1800 },
    );
  } catch {
    return null;
  }
}

const PCT = (v: number | null | undefined) =>
  v == null ? "—" : `${(v * 100).toFixed(1)}%`;

const TRILLION = (v: number | null | undefined) =>
  v == null ? "—" : `${(v / 1e12).toFixed(2)}조`;

export default async function ValueSegmentPage() {
  const data = await load();
  const kpi = data?.kpi;

  const cells: DenseSummaryCell[] = kpi
    ? [
        { label: "Holding 후보", value: String(kpi.candidates) },
        { label: "Discount > 20%", value: String(kpi.discount_gt_20), tone: "pos" },
        { label: "Premium > 20%", value: String(kpi.premium_gt_20), tone: "neg" },
        { label: "Mode", value: "Proxy (PBR)", tone: "amber" },
        { label: "Basis", value: "Sector-parity PBR" },
        { label: "Next step", value: "DART segment", delta: "pending" },
      ]
    : [];

  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "사업부문 분석", current: true }]}
        title="사업부문 (Segment) 분석"
        meta="SOTP proxy · Conglomerate discount · 지주사 필터"
      />
      {data ? <DenseSummary cells={cells} /> : null}
      <Panel
        title="SOTP 저평가 후보"
        muted="섹터 중위 PBR 대비 할인율 (proxy=True)"
        bodyPadding="p0"
      >
        {!data || data.rows.length === 0 ? (
          <EmptyState title="후보 없음" note="지주사/그룹/홀딩스 종목이 조회되지 않았습니다." />
        ) : (
          <table className="mini">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Sector</th>
                <th className="num">MCap</th>
                <th className="num">SOTP Proxy</th>
                <th className="num">Discount</th>
                <th className="num">PBR</th>
                <th className="num">Sector Med PBR</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.slice(0, 40).map((r) => (
                <tr key={r.symbol}>
                  <td>
                    <span className="ticker-name">{r.name || r.symbol}</span>
                    <span className="mono"> {r.symbol}</span>
                  </td>
                  <td>{r.sector ? <span className="chip accent">{r.sector}</span> : "—"}</td>
                  <td className="num">{TRILLION(r.market_cap)}</td>
                  <td className="num">{TRILLION(r.sotp_proxy)}</td>
                  <td
                    className="num"
                    style={{ color: r.discount > 0 ? "var(--pos)" : "var(--neg)" }}
                  >
                    {PCT(r.discount)}
                  </td>
                  <td className="num">{r.pbr?.toFixed(2) ?? "—"}</td>
                  <td className="num">{r.sector_median_pbr?.toFixed(2) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </>
  );
}
