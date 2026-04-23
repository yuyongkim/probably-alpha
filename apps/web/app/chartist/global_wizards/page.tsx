export const dynamic = "force-dynamic";
export default function Page() {
  return (
    <div>
      <div className="breadcrumb">Chartist <span className="sep">/</span> Global <span className="sep">/</span> <span className="current">Global Wizards</span></div>
      <div className="page-header">
        <div className="page-title-group">
          <h1>Global Wizards · 5 시장 통합</h1>
          <div className="page-meta">KR · US · JP · HK · CN × 6 Wizards</div>
        </div>
      </div>
      <div className="stub">
        <div className="stub-icon">🌐</div>
        <div className="stub-title">KIS 해외시세 어댑터 대기</div>
        <div className="stub-desc">KIS_APP_KEY / KIS_APP_SECRET 을 ~/.ky-platform/shared.env 에 설정하면 활성화. 목업 레이아웃은 통합 mockup 참조.</div>
        <div className="stub-chips"><span className="chip">KIS adapter skeleton</span><span className="chip accent">P1 Phase 6</span></div>
      </div>
    </div>
  );
}
