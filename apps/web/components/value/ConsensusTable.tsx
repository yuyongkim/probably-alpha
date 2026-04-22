// ConsensusTable — EPS/TP revision list.

import type { ConsensusRow } from "@/lib/value/mockData";

export function ConsensusTable({ rows }: { rows: ConsensusRow[] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Sector</th>
          <th className="num">EPS Rev %</th>
          <th className="num">TP Rev %</th>
          <th>Upgrade</th>
          <th className="num">커버 증권사</th>
          <th>Sentiment</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.ticker}>
            <td><span className="ticker-name">{r.ticker}</span></td>
            <td><span className="chip accent">{r.sector}</span></td>
            <td className="num" style={{ color: r.epsRevTone === "pos" ? "var(--pos)" : "var(--neg)" }}>{r.epsRev}</td>
            <td className="num" style={{ color: r.tpRevTone === "pos" ? "var(--pos)" : "var(--neg)" }}>{r.tpRev}</td>
            <td>
              <span className={`chip${r.upgradeTone === "pos" ? " pos" : r.upgradeTone === "neg" ? " neg" : ""}`}>
                {r.upgrade}
              </span>
            </td>
            <td className="num">{r.covers}</td>
            <td>
              <span className={`chip${r.sentimentTone === "pos" ? " pos" : r.sentimentTone === "neg" ? " neg" : ""}`}>
                {r.sentiment}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
