// UniverseTable — dense Top-N ticker table for Quant · Universe.

import type { UniverseResponse } from "@/types/quant";

export function UniverseTable({ rows }: { rows: UniverseResponse["rows"] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>#</th>
          <th>Symbol</th>
          <th>Name</th>
          <th>Mkt</th>
          <th>Sector</th>
          <th>Industry</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={r.symbol}>
            <td className="mono">{String(i + 1).padStart(3, "0")}</td>
            <td className="mono">{r.symbol}</td>
            <td><span className="ticker-name">{r.name ?? r.symbol}</span></td>
            <td><span className="chip">{r.market}</span></td>
            <td>{r.sector ?? "—"}</td>
            <td style={{ color: "var(--text-muted)" }}>{r.industry ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
