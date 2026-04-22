// MoatTable — Wide Moat list matching mockup `.mini` table.

import type { MoatRow } from "@/lib/value/mockData";

export function MoatTable({ rows }: { rows: MoatRow[] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>Ticker</th>
          <th>해자 Source</th>
          <th className="num">ROIC 10Y</th>
          <th className="num">ROIC 변동성</th>
          <th className="num">Margin 추세</th>
          <th>지속성</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.ticker}>
            <td><span className="ticker-name">{r.ticker}</span></td>
            <td>{r.source}</td>
            <td className="num">{r.roic}</td>
            <td className="num">{r.vol}</td>
            <td
              className="num"
              style={{
                color:
                  r.marginTone === "pos"
                    ? "var(--pos)"
                    : r.marginTone === "amber"
                      ? "var(--amber)"
                      : undefined,
              }}
            >
              {r.margin}
            </td>
            <td>
              <span className={`chip${r.labelTone === "pos" ? " pos" : r.labelTone === "amber" ? " amber" : ""}`}>
                {r.label}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
