// Research · Reproduce — academic paper reproducibility (dense mock + shell API fallback).
import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";

export const revalidate = 600;

const kpis = [
  { label: "재현 완료", value: "47", delta: "백테스트 코드 포함", tone: "pos" as const },
  { label: "재현 중", value: "12", delta: "WIP", tone: "amber" as const },
  { label: "재현 실패", value: "18", delta: "KR 시장 부적합", tone: "neg" as const },
  { label: "Live Strategy화", value: "6", delta: "실계좌 적용", tone: "pos" as const },
  { label: "평균 재현 기간", value: "4일", delta: "논문 → 백테스트" },
  { label: "공개 공유", value: "24", delta: "B2B 후 가능" },
];

const rows = [
  { title: "Quality Minus Junk", authors: "Asness-Frazzini-Pedersen", year: 2013, status: "Live", statusTone: "pos", us: "+6.2%", kr: "+5.8%", krTone: "pos", note: "소형주 제외 시 유의" },
  { title: "Betting Against Beta", authors: "Frazzini-Pedersen", year: 2014, status: "Live", statusTone: "pos", us: "+5.4%", kr: "+4.2%", krTone: "pos", note: "대형주 한정" },
  { title: "Time Series Momentum", authors: "Moskowitz-Ooi-Pedersen", year: 2012, status: "WIP", statusTone: "amber", us: "+12%", kr: "—", krTone: "default", note: "자산군 확장 중" },
  { title: "Value and Momentum", authors: "Asness-Moskowitz-Pedersen", year: 2013, status: "Live", statusTone: "pos", us: "+8.2%", kr: "+9.4%", krTone: "pos", note: "결합 효과 확증" },
  { title: "Short-Term Reversal", authors: "Jegadeesh", year: 1990, status: "Live", statusTone: "pos", us: "+3.2%", kr: "+4.8%", krTone: "pos", note: "KR 더 강함" },
  { title: "Accruals Anomaly", authors: "Sloan", year: 1996, status: "Failed", statusTone: "neg", us: "+2.4%", kr: "+0.8%", krTone: "default", note: "회계 차이" },
  { title: "Deep Value", authors: "Lev-Srivastava", year: 2022, status: "WIP", statusTone: "amber", us: "+7%", kr: "—", krTone: "default", note: "회계 재구성 중" },
  { title: "ESG Alpha", authors: "Pástor-Stambaugh-Taylor", year: 2021, status: "Failed", statusTone: "neg", us: "+1.8%", kr: "−0.4%", krTone: "default", note: "KR 데이터 부족" },
];

export default function Page() {
  return (
    <DensePage tab="Research" current="논문 재현" title="Academic Paper Reproducibility" meta="논문 결과 → 한국 시장 재현 → 내 전략화">
      <SummaryCards cells={kpis} />
      <div className="panel">
        <div className="panel-header"><h2>재현 중 논문</h2><span className="muted">진행 상태</span></div>
        <div className="panel-body p0">
          <table className="mini">
            <thead><tr><th>Paper</th><th>Authors</th><th>Year</th><th>Status</th><th className="num">원본</th><th className="num">재현 KR</th><th>Note</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.title}>
                  <td>{r.title}</td><td>{r.authors}</td><td>{r.year}</td>
                  <td><span className={`chip ${r.statusTone}`}>{r.status}</span></td>
                  <td className="num" style={{ color: "var(--pos)" }}>{r.us}</td>
                  <td className="num" style={r.krTone === "pos" ? { color: "var(--pos)" } : undefined}>{r.kr}</td>
                  <td>{r.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </DensePage>
  );
}
