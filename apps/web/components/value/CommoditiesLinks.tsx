// CommoditiesLinks — Commodity → KR ticker linkage table.

import type { CommLinkRow } from "@/lib/value/mockData";

export function CommoditiesLinks({ rows }: { rows: CommLinkRow[] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>Commodity</th>
          <th>Ticker</th>
          <th className="num">Beta</th>
          <th className="num">Corr 60D</th>
          <th>Direction</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            <td>{r.commodity}</td>
            <td><span className="ticker-name">{r.ticker}</span></td>
            <td className="num">{r.beta}</td>
            <td className="num">{r.corr}</td>
            <td>
              <span className={`chip${r.directionTone === "pos" ? " pos" : r.directionTone === "amber" ? " amber" : " neg"}`}>
                {r.direction}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
