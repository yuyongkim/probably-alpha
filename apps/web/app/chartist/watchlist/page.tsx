// Chartist · Watchlist — 관심종목 + 알람 (scaffold; full dense UI in a later sprint).
export const revalidate = 60;

export default function ChartistWatchlistPage() {
  return (
    <>
      <div className="breadcrumb">
        Chartist <span className="sep">/</span>
        <span className="current">관심종목</span>
      </div>
      <div className="page-header">
        <div className="page-title-group">
          <h1>관심종목 + 알람</h1>
          <div className="page-meta">SCAFFOLD · FULL UI 추후 스프린트</div>
        </div>
      </div>
      <div className="stub">
        <div className="stub-icon">★</div>
        <div className="stub-title">관심종목 · 알람</div>
        <div className="stub-desc">Alpha/Beta 조건 알람 + 가격/거래량 트리거. 곧 연결됩니다.</div>
      </div>
    </>
  );
}
