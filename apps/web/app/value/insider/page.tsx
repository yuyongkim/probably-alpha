// Value · Insider — DART 임원·주요주주 특정증권등 소유상황 (실데이터).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary, type DenseSummaryCell } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { EmptyState } from "@/components/shared/EmptyState";
import { fetchEnvelope } from "@/lib/api";
import type { InsiderResponse } from "@/types/value";

async function load(): Promise<InsiderResponse | null> {
  try {
    return await fetchEnvelope<InsiderResponse>(
      "/api/v1/value/insider?lookback_days=7",
      { revalidate: 600 },
    );
  } catch {
    return null;
  }
}

const KIND_LABELS: Record<string, string> = {
  insider: "임원ㆍ주요주주",
  bulk_ownership: "5% 대량보유",
  insider_plan: "거래계획 사전",
};

export default async function ValueInsiderPage() {
  const data = await load();
  const cells: DenseSummaryCell[] = data
    ? [
        { label: "7일 공시 총", value: String(data.kpi.total) },
        { label: "임원·주요주주", value: String(data.kpi.insider), tone: "pos" },
        { label: "5% 대량보유", value: String(data.kpi.bulk_ownership), tone: "neutral" },
        { label: "거래계획 사전", value: String(data.kpi.plan), tone: "amber" },
        { label: "Lookback", value: `${data.kpi.lookback_days}d` },
        { label: "Source", value: "DART" },
      ]
    : [];

  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "내부자 거래", current: true }]}
        title="내부자 거래 (DART)"
        meta="임원 · 주요주주 · 5% 대량보유 · 거래계획 사전공시"
      />
      {data ? <DenseSummary cells={cells} /> : null}
      <Panel
        title="최근 7일 내부자 공시"
        muted={data ? `${data.kpi.total}건` : undefined}
        bodyPadding="p0"
      >
        {!data || data.rows.length === 0 ? (
          <EmptyState title="공시 없음" note="선택한 기간에 임원/주요주주 공시가 없습니다." />
        ) : (
          <table className="mini">
            <thead>
              <tr>
                <th>Date</th>
                <th>회사</th>
                <th>구분</th>
                <th>공시명</th>
                <th>공시자</th>
                <th>Signal</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.slice(0, 60).map((r) => (
                <tr key={r.receipt_no || `${r.date}-${r.corp_code}`}>
                  <td className="mono">{r.date}</td>
                  <td>
                    <span className="ticker-name">{r.corp_name}</span>
                    {r.stock_code ? <span className="mono"> ({r.stock_code})</span> : null}
                  </td>
                  <td>
                    <span className="chip accent">{KIND_LABELS[r.kind] || r.kind}</span>
                  </td>
                  <td>{r.report_name}</td>
                  <td>{r.filer_name || "—"}</td>
                  <td>
                    <span className="chip">{r.signal}</span>
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
