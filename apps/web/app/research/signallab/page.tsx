import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { signalLabKpis, signalLabRows } from "@/lib/research/mockData";

export default function Page() {
  return (
    <DensePage tab="Research" current="Signal Lab" title="Signal Lab · 실험 신호" meta="IDEATION → QUICK BACKTEST → VALIDATE → PRODUCTIONIZE">
      <SummaryCards cells={signalLabKpis} />
      <div className="panel">
        <div className="panel-header"><h2>현재 실험 중 신호</h2><span className="muted">Validating + Testing</span></div>
        <div className="panel-body p0">
          <table className="mini">
            <thead><tr><th>Signal</th><th>Phase</th><th className="num">Sharpe</th><th className="num">IC</th><th className="num">Turnover</th><th className="num">일자</th><th>Next</th></tr></thead>
            <tbody>
              {signalLabRows.map((r) => (
                <tr key={r.signal}>
                  <td>{r.signal}</td>
                  <td><span className={`chip${r.phaseTone !== "default" ? ` ${r.phaseTone}` : ""}`}>{r.phase}</span></td>
                  <td className="num">{r.sharpe}</td>
                  <td className="num">{r.ic}</td>
                  <td className="num">{r.turnover}</td>
                  <td className="num">{r.days}</td>
                  <td>{r.next}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </DensePage>
  );
}
