// Execute · Overview — full dense mock (KIS keys absent).
import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { MarketStripRaw } from "@/components/execute/MarketStripRaw";
import { PositionsTable } from "@/components/execute/PositionsTable";
import { LiveBoardTable } from "@/components/execute/LiveBoardTable";
import { ActivityLogBlock } from "@/components/execute/ActivityLogBlock";
import { OverviewLower } from "@/components/execute/OverviewLower";
import {
  activityLog,
  liveQuotes,
  overviewKpis,
  overviewMarketCells,
  positions,
} from "@/lib/execute/mockData";

export const revalidate = 300;

export default function ExecuteOverviewPage() {
  return (
    <DensePage
      tab="Execute"
      current="계좌 Overview"
      title="계좌 Overview"
      meta="KIS OPEN API · 실시간 · 64082742-01 · 2026.04.22 15:30"
      subNav={[
        { label: "실계좌", active: true },
        { label: "모의계좌" }, { label: "국내" }, { label: "해외" }, { label: "파생" },
      ]}
    >
      <SummaryCards cells={overviewKpis} />
      <MarketStripRaw cells={overviewMarketCells} />
      <div className="grid-2" style={{ marginBottom: 10 }}>
        <div className="panel">
          <div className="panel-header"><h2>보유 포지션 — 전체 12</h2><span className="muted">QTY · AVG · LAST · P&L · 1D · STOP · TARGET · 전략 · HOLD</span></div>
          <div className="panel-body p0"><PositionsTable rows={positions} /></div>
        </div>
        <div className="panel">
          <div className="panel-header"><h2>Live WebSocket Board</h2><span className="muted">47 SYM · 12ms · ops.koreainvestment.com:21000</span></div>
          <div className="panel-body p0"><LiveBoardTable rows={liveQuotes} /></div>
        </div>
      </div>
      <OverviewLower />
      <div className="panel">
        <div className="panel-header"><h2>Activity Log</h2><span className="muted">LIVE · ORDERS · ALERTS · STRATEGIES · 최근 15</span></div>
        <div className="panel-body p0"><ActivityLogBlock items={activityLog} /></div>
      </div>
    </DensePage>
  );
}
