// Chartist · Backtest — real-data SEPA / Magic Formula / Quality+Momentum.
// Page is kept thin: loads data, composes panels from components/.
import { fetchEnvelope } from "@/lib/api";
import type {
  BacktestRun,
  BacktestListResponse,
} from "@/types/chartist";
import { MetricsCards } from "@/components/chartist/backtest/MetricsCards";
import { EquityChart } from "@/components/chartist/backtest/EquityChart";
import { TradesTable } from "@/components/chartist/backtest/TradesTable";
import { RunPicker } from "@/components/chartist/backtest/RunPicker";
import { SectorAttribution } from "@/components/chartist/backtest/SectorAttribution";

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
  } catch {
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
