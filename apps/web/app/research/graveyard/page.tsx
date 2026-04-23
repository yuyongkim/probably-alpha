import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { LocalStorageList } from "@/components/research/LocalStorageList";
import { graveyardKpis, graveyardRows } from "@/lib/research/mockData";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="Failed Strategies"
      title="Failed Strategies Graveyard"
      meta="버린 전략 · 실패 사유 · 교훈 아카이브"
    >
      <SummaryCards cells={graveyardKpis} />
      <div className="panel" style={{ marginTop: 14 }}>
        <div className="panel-header">
          <h2>참고 케이스</h2>
          <span className="muted">공공 샘플 · 내 post-mortem 은 아래에 저장</span>
        </div>
        <div className="panel-body p0">
          <table className="mini">
            <thead>
              <tr>
                <th>Date</th>
                <th>Strategy 개요</th>
                <th>Fail Reason</th>
                <th className="num">Live 기간</th>
                <th>교훈</th>
              </tr>
            </thead>
            <tbody>
              {graveyardRows.map((r) => (
                <tr key={`${r.date}-${r.name}`}>
                  <td className="mono">{r.date}</td>
                  <td>{r.name}</td>
                  <td>
                    <span
                      className={`chip${r.reasonTone !== "default" ? ` ${r.reasonTone}` : ""}`}
                    >
                      {r.reason}
                    </span>
                  </td>
                  <td className="num">{r.live}</td>
                  <td>{r.lesson}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ marginTop: 18 }}>
        <LocalStorageList
          storageKey="ky:research:graveyard"
          title="killed strategy"
          emptyCopy="아직 기록된 post-mortem 이 없습니다. 전략을 버릴 때 반드시 원인과 교훈을 남기세요."
          fields={[
            { name: "strategy", label: "전략", placeholder: "예: Earnings surprise momentum" },
            {
              name: "reason",
              label: "원인",
              type: "select",
              options: ["비용", "과최적화", "레짐", "유동성", "데이터", "기타"],
            },
            { name: "live_days", label: "Live 기간", placeholder: "3 months" },
            {
              name: "lesson",
              label: "교훈",
              placeholder: "다음에 이 실수를 반복하지 않기 위해 기억할 것",
              type: "textarea",
            },
          ]}
        />
      </div>
    </DensePage>
  );
}
