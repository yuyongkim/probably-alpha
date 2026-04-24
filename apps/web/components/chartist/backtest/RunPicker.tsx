// RunPicker — table of saved backtest runs that can be loaded into the page.
// Extracted from app/chartist/backtest/page.tsx on 2026-04-23.

import type { BacktestRunSummary } from "@/types/chartist";

export function RunPicker({
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
