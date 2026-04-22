// MeanRevTable — RSI(2) + BB 하단 후보 table.

import type { MeanRevRow } from "@/lib/quant/mockData";

export function MeanRevTable({ rows }: { rows: MeanRevRow[] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>Ticker</th>
          <th className="num">RSI(2)</th>
          <th className="num">BB %b</th>
          <th className="num">Z 20D</th>
          <th className="num">섹터 RS</th>
          <th className="num">Expected +5D</th>
          <th>Grade</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            <td><span className="ticker-name">{r.ticker}</span></td>
            <td className="num">{r.rsi}</td>
            <td className="num">{r.bb}</td>
            <td className="num">{r.z}</td>
            <td className="num">{r.rs}</td>
            <td className="num" style={{ color: "var(--pos)" }}>{r.expected}</td>
            <td><span className={`chip${r.gradeTone === "pos" ? " pos" : ""}`}>{r.grade}</span></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
