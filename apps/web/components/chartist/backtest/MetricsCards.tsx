// Metric KPI cards — compact summary of a backtest run.
import type { BacktestMetrics, BacktestRunSummary } from "@/types/chartist";

interface Props {
  metrics: BacktestMetrics;
  summary: Pick<BacktestRunSummary, "strategy" | "start" | "end" | "universe_size">;
}

function signedPct(v: number, digits = 2): string {
  return `${v >= 0 ? "+" : ""}${(v * 100).toFixed(digits)}%`;
}

function tone(v: number): string {
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

function fmtKrw(v: number): string {
  if (Math.abs(v) >= 1e8) return `${(v / 1e8).toFixed(2)}억`;
  if (Math.abs(v) >= 1e4) return `${(v / 1e4).toFixed(0)}만`;
  return v.toLocaleString();
}

export function MetricsCards({ metrics, summary }: Props) {
  const cards = [
    { label: "CAGR", value: signedPct(metrics.cagr), tone: tone(metrics.cagr) },
    { label: "총수익률", value: signedPct(metrics.total_return), tone: tone(metrics.total_return) },
    { label: "최대낙폭", value: signedPct(metrics.max_drawdown), tone: tone(metrics.max_drawdown) },
    { label: "Sharpe", value: metrics.sharpe.toFixed(2), tone: tone(metrics.sharpe) },
    { label: "Sortino", value: metrics.sortino.toFixed(2), tone: tone(metrics.sortino) },
    { label: "Calmar", value: metrics.calmar.toFixed(2), tone: tone(metrics.calmar) },
    { label: "승률", value: `${(metrics.win_rate * 100).toFixed(1)}%`, tone: "var(--neutral)" },
    { label: "Profit Factor", value: metrics.profit_factor.toFixed(2), tone: tone(metrics.profit_factor - 1) },
    { label: "Trade 수", value: metrics.n_trades.toString(), tone: "var(--neutral)" },
    { label: "평균 보유일", value: `${metrics.avg_holding_days.toFixed(1)}일`, tone: "var(--neutral)" },
    { label: "최종자산", value: fmtKrw(metrics.final_equity), tone: "var(--neutral)" },
    { label: "변동성 (연)", value: `${(metrics.volatility * 100).toFixed(1)}%`, tone: "var(--neutral)" },
  ];

  return (
    <div>
      <div
        className="rounded-md border px-3 py-2 mb-3 flex items-baseline justify-between"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div>
          <div className="display text-base">{summary.strategy}</div>
          <div className="text-[11px] text-[color:var(--fg-muted)]">
            {summary.start} → {summary.end} · Universe {summary.universe_size.toLocaleString()}
          </div>
        </div>
        <div className="text-[10px] text-[color:var(--fg-muted)]">
          {metrics.n_days.toLocaleString()} 거래일
        </div>
      </div>
      <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
        {cards.map((c) => (
          <div
            key={c.label}
            className="rounded-md border px-3 py-2"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}
          >
            <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--fg-muted)]">
              {c.label}
            </div>
            <div className="mono text-[15px] mt-1 tabular-nums" style={{ color: c.tone }}>
              {c.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
