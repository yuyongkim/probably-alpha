// SummaryCards — mockup `.summary-row` + `.summary-card` grid (6 KPI boxes).
// Presentational; takes raw cell definitions.

export interface RawSummaryCell {
  label: string;
  value: string;
  delta?: string;
  tone?: "pos" | "neg" | "amber";
}

interface Props {
  cells: RawSummaryCell[];
  className?: string;
}

export function SummaryCards({ cells, className }: Props) {
  return (
    <div className={`summary-row ${className ?? ""}`.trim()}>
      {cells.map((c) => (
        <div key={c.label} className="summary-card">
          <div className="label">{c.label}</div>
          <div className="value">{c.value}</div>
          {c.delta ? (
            <div className={`delta tnum${c.tone ? ` ${c.tone}` : ""}`}>
              {c.delta}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
