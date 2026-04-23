// Value · Buyback — 자사주 공시 실데이터 (DART).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary, type DenseSummaryCell } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { EmptyState } from "@/components/shared/EmptyState";
import { fetchEnvelope } from "@/lib/api";
import type { BuybackResponse } from "@/types/value";

async function load(): Promise<BuybackResponse | null> {
  try {
    return await fetchEnvelope<BuybackResponse>(
      "/api/v1/value/buyback?lookback_days=30",
      { revalidate: 600 },
    );
  } catch {
    return null;
  }
}

const ACTION_LABEL: Record<string, string> = {
  buyback: "취득",
  dispose: "처분",
  cancel: "소각",
  trust: "신탁",
  other: "기타",
};

const ACTION_TONE: Record<string, string> = {
  buyback: " pos",
  cancel: " pos",
  trust: "",
  dispose: " neg",
  other: "",
};

export default async function ValueBuybackPage() {
  const data = await load();
  const cells: DenseSummaryCell[] = data
    ? [
        { label: "30일 공시 총", value: String(data.kpi.total) },
        { label: "취득 결정", value: String(data.kpi.buyback_decision), tone: "pos" },
        { label: "취득 결과", value: String(data.kpi.buyback_result), tone: "pos" },
        { label: "소각", value: String(data.kpi.cancel), tone: "pos" },
        { label: "처분", value: String(data.kpi.dispose), tone: "neg" },
        { label: "신탁", value: String(data.kpi.trust) },
      ]
    : [];

  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "자사주 매입", current: true }]}
        title="자사주 매입 (Buyback) 스크리너"
        meta="주주환원 · 저평가 인식 · 소각 vs 금고주"
      />
      {data ? <DenseSummary cells={cells} /> : null}
      <Panel
        title="최근 30일 자사주 공시"
        muted={data ? `${data.kpi.total}건` : undefined}
        bodyPadding="p0"
      >
        {!data || data.rows.length === 0 ? (
          <EmptyState title="공시 없음" note="선택한 기간에 자사주 공시가 없습니다." />
        ) : (
          <table className="mini">
            <thead>
              <tr>
                <th>Date</th>
                <th>회사</th>
                <th>유형</th>
                <th>상태</th>
                <th>공시명</th>
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
                    <span className={`chip${ACTION_TONE[r.action] || ""}`}>
                      {ACTION_LABEL[r.action] || r.action}
                    </span>
                  </td>
                  <td>
                    <span className={`chip${r.status === "result" ? " pos" : ""}`}>
                      {r.status === "result" ? "결과" : "결정"}
                    </span>
                  </td>
                  <td>{r.report_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </>
  );
}
