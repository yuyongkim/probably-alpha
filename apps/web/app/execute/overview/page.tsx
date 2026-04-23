// Execute · Overview — KIS OAuth health + mock balance/positions.
// As of 2026-04-22 keys are live; balance TR not yet wired so positions
// remain mocked until inquire-balance lands.
import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { MarketStripRaw } from "@/components/execute/MarketStripRaw";
import { PositionsTable } from "@/components/execute/PositionsTable";
import { LiveBoardTable } from "@/components/execute/LiveBoardTable";
import { ActivityLogBlock } from "@/components/execute/ActivityLogBlock";
import { OverviewLower } from "@/components/execute/OverviewLower";
import { fetchEnvelope } from "@/lib/api";
import {
  activityLog,
  liveQuotes,
  overviewKpis,
  overviewMarketCells,
  positions,
} from "@/lib/execute/mockData";

export const revalidate = 300;

interface OverviewLive {
  account_no: string | null;
  product_code: string;
  env: string;
  health: {
    ok: boolean;
    source_id: string;
    latency_ms: number | null;
    last_error: string | null;
    token_cached?: boolean;
  };
  positions: unknown[];
  note: string;
}

async function load(): Promise<OverviewLive | null> {
  try {
    return await fetchEnvelope<OverviewLive>("/api/v1/execute/overview", {
      revalidate: 60,
    });
  } catch {
    return null;
  }
}

export default async function ExecuteOverviewPage() {
  const live = await load();
  const healthOk = live?.health?.ok === true;
  const latency = live?.health?.latency_ms;
  const acctFragment = live?.account_no
    ? `${live.account_no}-${live.product_code ?? "01"}`
    : "계좌 미설정";
  const statusPill = healthOk
    ? `KIS OAuth OK · ${latency != null ? `${latency.toFixed(0)}ms` : "cached"}`
    : `KIS OAuth FAIL · ${live?.health?.last_error ?? "unknown"}`;
  const meta = `KIS OPEN API · ${live?.env ?? "?"} · ${acctFragment} · ${statusPill}`;

  return (
    <DensePage
      tab="Execute"
      current="계좌 Overview"
      title="계좌 Overview"
      meta={meta}
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
