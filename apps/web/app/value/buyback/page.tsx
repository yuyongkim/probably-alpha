// Value · Buyback — 자사주 매입 스크리너 (mock).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { BUYBACK_KPI, BUYBACK_ROWS } from "@/lib/value/mockData";

export default function ValueBuybackPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "자사주 매입", current: true }]}
        title="자사주 매입 (Buyback) 스크리너"
        meta="주주환원 · 저평가 인식 · 소각 vs 금고주"
      />
      <DenseSummary cells={BUYBACK_KPI} />
      <Panel title="주목할 Buyback" muted="소각 / 대규모 매입" bodyPadding="p0">
        <table className="mini">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>유형</th>
              <th className="num">규모</th>
              <th className="num">시가%</th>
              <th>기간</th>
              <th>진행률</th>
            </tr>
          </thead>
          <tbody>
            {BUYBACK_ROWS.map((r) => (
              <tr key={r.ticker}>
                <td><span className="ticker-name">{r.ticker}</span></td>
                <td><span className={`chip${r.type === "소각" ? " pos" : ""}`}>{r.type}</span></td>
                <td className="num">{r.size}</td>
                <td className="num">{r.pct}</td>
                <td>{r.period}</td>
                <td><span className={`chip${r.progressTone === "pos" ? " pos" : ""}`}>{r.progress}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </>
  );
}
