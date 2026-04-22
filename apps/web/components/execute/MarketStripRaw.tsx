// MarketStripRaw — mockup `.market-strip` (8-cell account-specific strip).
interface Cell {
  label: string;
  value: string;
  delta?: string;
  tone?: "pos" | "neg";
}

export function MarketStripRaw({ cells }: { cells: Cell[] }) {
  return (
    <div className="market-strip">
      {cells.map((c) => (
        <div key={c.label} className="market-cell">
          <span className="mc-label">{c.label}</span>
          <span className="mc-value">{c.value}</span>
          {c.delta ? (
            <span className={`mc-delta${c.tone ? ` ${c.tone}` : ""}`}>{c.delta}</span>
          ) : null}
        </div>
      ))}
    </div>
  );
}
