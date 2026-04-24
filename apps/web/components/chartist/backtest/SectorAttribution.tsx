// SectorAttribution — table of wins/losses and net P/L by sector for a run.
// Extracted from app/chartist/backtest/page.tsx on 2026-04-23.

import type { BacktestRun } from "@/types/chartist";

export function SectorAttribution({
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
