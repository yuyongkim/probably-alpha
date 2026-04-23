// Execute · KIS Backtester — live list of backtest runs from chartist engine.
// Wired to GET /api/v1/chartist/backtest/list (shared with Chartist tab).
import Link from "next/link";
import { DensePage } from "@/components/shared/DensePage";
import { EmptyState } from "@/components/shared/EmptyState";
import { StubBlock } from "@/components/execute/StubBlock";
import { fetchEnvelope } from "@/lib/api";
import type { BacktestListResponse } from "@/types/chartist";

export const revalidate = 60;

async function loadRuns(): Promise<BacktestListResponse | null> {
  try {
    return await fetchEnvelope<BacktestListResponse>(
      "/api/v1/chartist/backtest/list?limit=12",
      { revalidate: 60 },
    );
  } catch {
    return null;
  }
}

const fmtPct = (n: number) => `${(n * 100).toFixed(1)}%`;
const fmtNum = (n: number) => n.toLocaleString();

export default async function Page() {
  const list = await loadRuns();
  const runs = list?.runs ?? [];

  return (
    <DensePage
      tab="Execute"
      current="KIS Backtester"
      title="KIS Backtester"
      meta="SEPA · Magic Formula · Quality+Momentum · Value-QMJ · cost-adjusted"
    >
      {runs.length === 0 ? (
        <EmptyState
          title="저장된 백테스트 런이 없습니다"
          note="Chartist 탭의 Backtest 페이지에서 신규 런을 실행하세요."
          hint="GET /api/v1/chartist/backtest/list"
        />
      ) : (
        <div className="panel">
          <div className="panel-header">
            <h2>최근 백테스트 {runs.length}건</h2>
            <span className="muted">cost-adjusted · 실데이터 · 클릭 시 상세</span>
          </div>
          <div className="panel-body p0">
            <table className="mini">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Strategy</th>
                  <th>기간</th>
                  <th style={{ textAlign: "right" }}>Trades</th>
                  <th style={{ textAlign: "right" }}>CAGR</th>
                  <th style={{ textAlign: "right" }}>MDD</th>
                  <th style={{ textAlign: "right" }}>Sharpe</th>
                  <th style={{ textAlign: "right" }}>Win%</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.run_id}>
                    <td className="mono">
                      <Link href={`/chartist/backtest?run_id=${r.run_id}`}>
                        {r.run_id}
                      </Link>
                    </td>
                    <td>{r.strategy ?? "—"}</td>
                    <td className="mono">{r.start}→{r.end}</td>
                    <td style={{ textAlign: "right" }}>{fmtNum(r.n_trades)}</td>
                    <td style={{ textAlign: "right", color: r.cagr >= 0 ? "var(--pos)" : "var(--neg)" }}>{fmtPct(r.cagr)}</td>
                    <td style={{ textAlign: "right", color: "var(--neg)" }}>{fmtPct(r.max_drawdown)}</td>
                    <td style={{ textAlign: "right" }}>{r.sharpe.toFixed(2)}</td>
                    <td style={{ textAlign: "right" }}>{fmtPct(r.win_rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <StubBlock
          icon="K"
          title="파라미터 최적화 (Grid / Random Search)"
          desc="KIS 샘플 레포의 optimizer 흡수 예정. 현재는 ky_core.backtest 엔진의 단일 런만 지원."
          chips={["ROADMAP"]}
        />
      </div>
    </DensePage>
  );
}
