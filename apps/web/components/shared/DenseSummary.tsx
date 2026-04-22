// DenseSummary — 6-cell KPI summary row matching mockup `.summary-row`.
// Uses raw globals.css classes.

export interface DenseSummaryCell {
  label: string;
  value: string;
  delta?: string;
  tone?: "pos" | "neg" | "amber" | "neutral";
}

export function DenseSummary({ cells }: { cells: DenseSummaryCell[] }) {
  return (
    <div className="summary-row">
      {cells.map((c) => (
        <div key={c.label} className="summary-card">
          <div className="label">{c.label}</div>
          <div className="value">{c.value}</div>
          {c.delta ? (
            <div
              className={`delta tnum${
                c.tone === "pos"
                  ? " pos"
                  : c.tone === "neg"
                    ? " neg"
                    : c.tone === "amber"
                      ? " amber"
                      : ""
              }`}
            >
              {c.delta}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
