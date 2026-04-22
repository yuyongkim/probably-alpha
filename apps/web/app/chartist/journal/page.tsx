// Chartist · Journal — 매매일지 (scaffold; full dense UI in a later sprint).
export const revalidate = 60;

export default function ChartistJournalPage() {
  return (
    <>
      <div className="breadcrumb">
        Chartist <span className="sep">/</span>
        <span className="current">매매일지</span>
      </div>
      <div className="page-header">
        <div className="page-title-group">
          <h1>매매일지</h1>
          <div className="page-meta">SCAFFOLD · FULL UI 추후 스프린트</div>
        </div>
      </div>
      <div className="stub">
        <div className="stub-icon">✎</div>
        <div className="stub-title">매매일지는 곧 연결됩니다</div>
        <div className="stub-desc">
          진입/청산/감정 로그 + Playbook 매칭. localStorage → 서버 저장.
        </div>
      </div>
    </>
  );
}
