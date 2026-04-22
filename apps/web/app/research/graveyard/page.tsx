import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { graveyardKpis, graveyardRows } from "@/lib/research/mockData";

export default function Page() {
  return (
    <DensePage tab="Research" current="Failed Strategies" title="Failed Strategies Graveyard" meta="버린 전략 · 실패 사유 · 교훈 아카이브">
      <SummaryCards cells={graveyardKpis} />
      <div className="panel">
        <div className="panel-header"><h2>실패 전략 아카이브</h2><span className="muted">교훈 먼저, 이름은 비공개</span></div>
        <div className="panel-body p0">
          <table className="mini">
            <thead><tr><th>Date</th><th>Strategy 개요</th><th>Fail Reason</th><th className="num">Live 기간</th><th>교훈</th></tr></thead>
            <tbody>
              {graveyardRows.map((r) => (
                <tr key={`${r.date}-${r.name}`}>
                  <td className="mono">{r.date}</td>
                  <td>{r.name}</td>
                  <td><span className={`chip${r.reasonTone !== "default" ? ` ${r.reasonTone}` : ""}`}>{r.reason}</span></td>
                  <td className="num">{r.live}</td>
                  <td>{r.lesson}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </DensePage>
  );
}
