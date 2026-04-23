import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { LocalStorageList } from "@/components/research/LocalStorageList";
import { signalLabKpis, signalLabRows } from "@/lib/research/mockData";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="Signal Lab"
      title="Signal Lab · 실험 신호"
      meta="IDEATION → QUICK TEST → VALIDATING → PRODUCTION"
    >
      <SummaryCards cells={signalLabKpis} />
      <div className="panel" style={{ marginTop: 14 }}>
        <div className="panel-header">
          <h2>샘플 신호 (참고용)</h2>
          <span className="muted">아래 내 실험은 브라우저 로컬에만 저장됨</span>
        </div>
        <div className="panel-body p0">
          <table className="mini">
            <thead>
              <tr>
                <th>Signal</th>
                <th>Phase</th>
                <th className="num">Sharpe</th>
                <th className="num">IC</th>
                <th className="num">Turnover</th>
                <th className="num">일자</th>
                <th>Next</th>
              </tr>
            </thead>
            <tbody>
              {signalLabRows.map((r) => (
                <tr key={r.signal}>
                  <td>{r.signal}</td>
                  <td>
                    <span
                      className={`chip${r.phaseTone !== "default" ? ` ${r.phaseTone}` : ""}`}
                    >
                      {r.phase}
                    </span>
                  </td>
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

      <div style={{ marginTop: 18 }}>
        <LocalStorageList
          storageKey="ky:research:signallab"
          title="signal experiment"
          emptyCopy="아직 저장된 실험이 없습니다. 아이디어 → Quick Test → Validating → Production 흐름으로 기록하세요."
          fields={[
            { name: "signal", label: "시그널 이름", placeholder: "예: 외인 연속 순매수" },
            {
              name: "phase",
              label: "단계",
              type: "select",
              options: ["Idea", "Quick Test", "Validating", "Production", "Killed"],
            },
            { name: "sharpe", label: "Sharpe", placeholder: "1.8" },
            { name: "ic", label: "IC", placeholder: "0.12" },
            { name: "turnover", label: "Turnover", placeholder: "저/중/고" },
            {
              name: "note",
              label: "메모",
              placeholder: "현재까지 관찰된 특징, 다음 단계",
              type: "textarea",
            },
          ]}
        />
      </div>
    </DensePage>
  );
}
