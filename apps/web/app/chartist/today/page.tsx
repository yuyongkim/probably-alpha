// Chartist · Today
// Placeholder page — wired in Phase 3 via hooks/useChartistToday.ts
// See CONTRIBUTING.md §1 (page files ≤100 lines).
export default function ChartistTodayPage() {
  return (
    <div>
      <h1 className="display text-3xl mb-2">오늘의 시장</h1>
      <p className="text-sm text-[color:var(--fg-muted)] mb-6">
        섹터 로테이션 · 리더 스캔 · 마지막 백테스트 요약.
      </p>
      <div className="p-6 rounded-md border border-border bg-[color:var(--surface)]">
        <div className="text-[color:var(--accent)] text-xs uppercase tracking-widest mb-2">
          Coming in Phase 3
        </div>
        <p className="text-sm">
          이 페이지는 <code className="mono">/api/v1/chartist/today</code> 에서 데이터를 받아
          SummaryRow · DenseTable · QuoteStrip 컴포넌트를 조립합니다.
        </p>
      </div>
    </div>
  );
}
