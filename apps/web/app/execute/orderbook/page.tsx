export const dynamic = "force-dynamic";
export default function Page() {
  return (
    <div>
      <div className="breadcrumb">Execute <span className="sep">/</span> <span className="current">호가창 L2 + 체결강도</span></div>
      <div className="page-header">
        <div className="page-title-group">
          <h1>호가창 L2 + 체결강도</h1>
          <div className="page-meta">KIS WEBSOCKET · 10-LEVEL DEPTH · TICK-BY-TICK</div>
        </div>
      </div>
      <div className="stub">
        <div className="stub-icon">⚡</div>
        <div className="stub-title">KIS 실시간 데이터 대기</div>
        <div className="stub-desc">mockup 의 dense 호가창/알고리즘 주문 레이아웃 구현 준비 완료. KIS 키 세팅 시 실시간으로 전환됩니다.</div>
        <div className="stub-chips"><span className="chip">KIS WebSocket</span><span className="chip accent">Phase 6</span></div>
      </div>
    </div>
  );
}
