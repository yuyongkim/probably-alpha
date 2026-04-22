// InsiderTable — DART insider-trading list.

import type { InsiderRow } from "@/lib/value/mockData";

export function InsiderTable({ rows }: { rows: InsiderRow[] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>Date</th>
          <th>Ticker</th>
          <th>Who</th>
          <th>Type</th>
          <th className="num">규모</th>
          <th className="num">지분변동</th>
          <th>Signal</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            <td className="mono">{r.date}</td>
            <td><span className="ticker-name">{r.ticker}</span></td>
            <td>{r.who}</td>
            <td><span className={`chip${r.type === "매수" ? " pos" : " neg"}`}>{r.type}</span></td>
            <td className="num">{r.size}</td>
            <td className="num" style={{ color: r.stakeTone === "pos" ? "var(--pos)" : "var(--neg)" }}>{r.stake}</td>
            <td>
              <span className={`chip${r.signalTone === "pos" ? " pos" : r.signalTone === "neg" ? " neg" : ""}`}>
                {r.signal}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
