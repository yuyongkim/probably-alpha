// MagicTable — Greenblatt magic formula top-N presentation.

import type { AcademicRow } from "@/types/quant";

export function MagicTable({ rows }: { rows: AcademicRow[] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>#</th>
          <th>Ticker</th>
          <th>Sector</th>
          <th className="num">EY</th>
          <th className="num">ROC</th>
          <th className="num">Magic Score</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={r.symbol}>
            <td className="mono">{String(i + 1).padStart(2, "0")}</td>
            <td>
              <span className="ticker-name">{r.name ?? r.symbol}</span>
              <span className="mono" style={{ marginLeft: 6, color: "var(--text-muted)" }}>
                {r.symbol}
              </span>
            </td>
            <td>{r.sector ? <span className="chip accent">{r.sector}</span> : "—"}</td>
            <td className="num">{r.earnings_yield != null ? `${(r.earnings_yield * 100).toFixed(1)}%` : "—"}</td>
            <td className="num">{r.roc != null ? `${(r.roc * 100).toFixed(1)}%` : "—"}</td>
            <td className="num" style={{ fontWeight: 600 }}>
              {r.magic_score?.toFixed(2) ?? "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
