// LeaderTable — dense mockup-style top-N ranking table for Value screeners.
// Unlike components/value/LeaderList.tsx (loose), this matches `.mini` layout.

import type { LeaderRow } from "@/types/value";

interface Props {
  rows: LeaderRow[];
  metricKey: string;
  metricHeader: string;
  metricFormat?: (v: unknown) => string;
  metricDigits?: number;
  highlightPositive?: boolean;
}

const num = (v: unknown, digits = 2): string => {
  if (typeof v !== "number") return "—";
  return v.toLocaleString(undefined, { maximumFractionDigits: digits });
};

export function LeaderTable({
  rows,
  metricKey,
  metricHeader,
  metricFormat,
  metricDigits = 2,
  highlightPositive = false,
}: Props) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>Sym</th>
          <th>Name</th>
          <th>Sector</th>
          <th className="num">Close</th>
          <th className="num">{metricHeader}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const raw = r[metricKey as keyof LeaderRow];
          const display = metricFormat ? metricFormat(raw) : num(raw, metricDigits);
          const positive = typeof raw === "number" && raw > 0;
          return (
            <tr key={r.symbol}>
              <td className="mono">{r.symbol}</td>
              <td><span className="ticker-name">{r.name ?? r.symbol}</span></td>
              <td>{r.sector ? <span className="chip accent">{r.sector}</span> : "—"}</td>
              <td className="num">{r.close?.toLocaleString() ?? "—"}</td>
              <td
                className="num"
                style={{
                  fontWeight: 600,
                  color: highlightPositive && positive ? "var(--pos)" : undefined,
                }}
              >
                {display}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
