// PositionsTable — renders mockup `.mini` table for open positions.
import type { Position } from "@/types/execute";

export function PositionsTable({ rows }: { rows: Position[] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>Ticker</th><th>AST</th><th className="num">Qty</th><th className="num">Avg</th>
          <th className="num">Last</th><th className="num">P&L</th><th className="num">%</th>
          <th className="num">1D</th><th className="num">Stop</th><th className="num">Target</th>
          <th>Strategy</th><th className="num">Hold</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((p) => {
          const toneColor = p.tone === "pos" ? "var(--pos)" : p.tone === "neg" ? "var(--neg)" : undefined;
          const change1dColor = p.change1d.startsWith("−") ? "var(--neg)" : "var(--pos)";
          return (
            <tr key={p.code}>
              <td>
                <span className="ticker-name">{p.ticker}</span>
                <span className="mono" style={{ marginLeft: 6, color: "var(--text-muted)" }}>{p.code}</span>
              </td>
              <td><span className={`chip ${p.market === "KR" ? "accent" : "amber"}`}>{p.market}</span></td>
              <td className="num">{p.qty}</td>
              <td className="num">{p.avg}</td>
              <td className="num">{p.last}</td>
              <td className="num" style={{ color: toneColor, fontWeight: 600 }}>{p.pnl}</td>
              <td className="num" style={{ color: toneColor }}>{p.pct}</td>
              <td className="num" style={{ color: change1dColor }}>{p.change1d}</td>
              <td className="num">{p.stop}</td>
              <td className="num">{p.target}</td>
              <td>
                <span className={`chip${p.strategyTone === "accent" ? " accent" : p.strategyTone === "amber" ? " amber" : ""}`}>
                  {p.strategy}
                </span>
              </td>
              <td className="num">{p.hold}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
