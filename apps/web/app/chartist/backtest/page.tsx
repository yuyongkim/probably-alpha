// Chartist · Backtest — real-data SEPA / Magic Formula / Quality+Momentum.
import { fetchEnvelope } from "@/lib/api";
import type {
  BacktestRun,
  BacktestListResponse,
  BacktestRunSummary,
} from "@/types/chartist";
import { MetricsCards } from "@/components/chartist/backtest/MetricsCards";
import { EquityChart } from "@/components/chartist/backtest/EquityChart";
import { TradesTable } from "@/components/chartist/backtest/TradesTable";

export const revalidate = 60;
export const dynamic = "force-dynamic";

interface PageProps {
  searchParams?: Promise<{ run_id?: string; strategy?: string }>;
}

export default async function ChartistBacktestPage({ searchParams }: PageProps) {
  const params = (await searchParams) ?? {};
  const query = new URLSearchParams();
  if (params.run_id) query.set("run_id", params.run_id);
  else if (params.strategy) query.set("strategy", params.strategy);
  query.set("trim_curve", "600");

  let run: BacktestRun | null = null;
  let runError: string | null = null;
  try {
    run = await fetchEnvelope<BacktestRun>(
      `/api/v1/chartist/backtest?${query.toString()}`,
    );
  } catch (exc) {
    runError = exc instanceof Error ? exc.message : String(exc);
  }

  let list: BacktestListResponse = { count: 0, runs: [] };
  try {
    list = await fetchEnvelope<BacktestListResponse>(
      "/api/v1/chartist/backtest/list?limit=30",
    );
  } catch (exc) {
    // list is optional; fall through
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="display text-3xl">Backtest</h1>
        <div className="text-xs text-[color:var(--fg-muted)] mt-1">
          SEPA · Magic Formula · Quality+Momentum · Value-QMJ — 실데이터 (ky.db OHLCV + financials_pit, cost-adjusted)
        </div>
      </div>

      <RunPicker list={list.runs} activeRunId={run?.run_id} />

      {run ? (
        <>
          <MetricsCards
            metrics={run.metrics}
            summary={{
              strategy: run.config.strategy_name,
              start: run.config.start,
              end: run.config.end,
              universe_size: run.universe_size,
            }}
          />
          <EquityChart
            equity={run.equity_curve}
            benchmark={run.benchmark_curve}
            initialCash={run.config.initial_cash}
          />
          <TradesTable trades={run.trades} />
          <SectorAttribution attribution={run.sector_attribution} />
        </>
      ) : (
        <div
          className="rounded-md border px-4 py-6 text-[12px] text-[color:var(--fg-muted)]"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}
        >
          No backtest run selected.{" "}
          {runError ? (
            <span className="text-[color:var(--neg)]">{runError}</span>
          ) : (
            <span>Use the picker above to load a saved run.</span>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------- //

function RunPicker({
  list,
  activeRunId,
}: {
  list: BacktestRunSummary[];
  activeRunId: string | undefined;
}) {
  if (!list.length) {
    return (
      <div
        className="rounded-md border px-3 py-2 text-[11px] text-[color:var(--fg-muted)]"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        No saved backtest runs yet. Kick one off with{" "}
        <code className="mono text-[10px]">
          python scripts/run_backtest.py --strategy sepa ...
        </code>
      </div>
    );
  }
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-sm">저장된 Run</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          {list.length} runs
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11.5px] border-collapse">
          <thead>
            <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
              <th className="py-1.5 px-2 text-left border-b">전략</th>
              <th className="py-1.5 px-2 text-left border-b">기간</th>
              <th className="py-1.5 px-2 text-right border-b">CAGR</th>
              <th className="py-1.5 px-2 text-right border-b">MDD</th>
              <th className="py-1.5 px-2 text-right border-b">Sharpe</th>
              <th className="py-1.5 px-2 text-right border-b">Trades</th>
              <th className="py-1.5 px-2 text-left border-b">Run ID</th>
            </tr>
          </thead>
          <tbody>
            {list.map((r) => {
              const active = r.run_id === activeRunId;
              return (
                <tr
                  key={r.run_id}
                  style={{
                    borderBottom: "1px solid var(--border-soft)",
                    background: active ? "var(--surface-2)" : undefined,
                  }}
                >
                  <td className="py-1 px-2">{r.strategy}</td>
                  <td className="py-1 px-2 mono text-[10.5px] text-[color:var(--fg-muted)]">
                    {r.start} → {r.end}
                  </td>
                  <td
                    className="py-1 px-2 mono text-[11px] text-right tabular-nums"
                    style={{ color: r.cagr >= 0 ? "var(--pos)" : "var(--neg)" }}
                  >
                    {(r.cagr * 100).toFixed(2)}%
                  </td>
                  <td className="py-1 px-2 mono text-[11px] text-right tabular-nums"
                      style={{ color: "var(--neg)" }}>
                    {(r.max_drawdown * 100).toFixed(2)}%
                  </td>
                  <td className="py-1 px-2 mono text-[11px] text-right tabular-nums">
                    {r.sharpe.toFixed(2)}
                  </td>
                  <td className="py-1 px-2 mono text-[11px] text-right tabular-nums">
                    {r.n_trades}
                  </td>
                  <td className="py-1 px-2">
                    <a
                      href={`/chartist/backtest?run_id=${r.run_id}`}
                      className="text-[color:var(--accent)] hover:underline mono text-[10.5px]"
                    >
                      {r.run_id}
                    </a>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SectorAttribution({
  attribution,
}: {
  attribution: BacktestRun["sector_attribution"];
}) {
  const rows = Object.entries(attribution)
    .map(([sector, a]) => ({ sector, ...a }))
    .sort((a, b) => b.gross_pnl - a.gross_pnl);
  if (!rows.length) return null;
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">섹터 기여도</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          {rows.length} 섹터
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11.5px] border-collapse">
          <thead>
            <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
              <th className="py-1.5 px-2 text-left border-b">섹터</th>
              <th className="py-1.5 px-2 text-right border-b">Trades</th>
              <th className="py-1.5 px-2 text-right border-b">Wins</th>
              <th className="py-1.5 px-2 text-right border-b">Losses</th>
              <th className="py-1.5 px-2 text-right border-b">승률</th>
              <th className="py-1.5 px-2 text-right border-b">순손익 (KRW)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.sector}
                  style={{ borderBottom: "1px solid var(--border-soft)" }}>
                <td className="py-1 px-2">{r.sector}</td>
                <td className="py-1 px-2 mono text-[11px] text-right tabular-nums">{r.n_trades}</td>
                <td className="py-1 px-2 mono text-[11px] text-right tabular-nums text-[color:var(--pos)]">
                  {r.wins}
                </td>
                <td className="py-1 px-2 mono text-[11px] text-right tabular-nums text-[color:var(--neg)]">
                  {r.losses}
                </td>
                <td className="py-1 px-2 mono text-[11px] text-right tabular-nums">
                  {(r.win_rate * 100).toFixed(1)}%
                </td>
                <td
                  className="py-1 px-2 mono text-[11px] text-right tabular-nums"
                  style={{ color: r.gross_pnl >= 0 ? "var(--pos)" : "var(--neg)" }}
                >
                  {r.gross_pnl >= 0 ? "+" : ""}
                  {Math.round(r.gross_pnl).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
