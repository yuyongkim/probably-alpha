// PairsTable — cointegration pair-trading list.

import type { PairRow } from "@/lib/quant/mockData";

export function PairsTable({ rows }: { rows: PairRow[] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>Long</th>
          <th>Short</th>
          <th className="num">Z-Score</th>
          <th className="num">Half-life</th>
          <th className="num">Corr</th>
          <th className="num">P-value</th>
          <th>Signal</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((p, i) => (
          <tr key={i}>
            <td><span className="ticker-name">{p.long}</span></td>
            <td><span className="ticker-name">{p.short}</span></td>
            <td className="num" style={{ color: p.zTone === "pos" ? "var(--pos)" : p.zTone === "neg" ? "var(--neg)" : undefined }}>{p.z}</td>
            <td className="num">{p.halfLife}</td>
            <td className="num">{p.corr}</td>
            <td className="num">{p.pValue}</td>
            <td>
              <span className={`chip${p.signalTone === "pos" ? " pos" : p.signalTone === "neg" ? " neg" : ""}`}>
                {p.signal}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
