// MarketStripPanel — 8-cell market context strip matching mockup `.market-strip`.
// Unlike components/chartist/today/MarketStrip.tsx (which uses tokens via style),
// this version uses the raw globals.css classes for dense identical look.

export interface MarketStripCell {
  label: string;
  value: string;
  delta?: string;
  tone?: "pos" | "neg" | "amber" | "neutral";
}

export function MarketStripPanel({ cells }: { cells: MarketStripCell[] }) {
  return (
    <div className="market-strip">
      {cells.map((c) => (
        <div key={c.label} className="market-cell">
          <span className="mc-label">{c.label}</span>
          <span className="mc-value">{c.value}</span>
          {c.delta ? (
            <span
              className={`mc-delta${
                c.tone === "pos"
                  ? " pos"
                  : c.tone === "neg"
                    ? " neg"
                    : ""
              }`}
              style={c.tone === "amber" ? { color: "var(--amber)" } : undefined}
            >
              {c.delta}
            </span>
          ) : null}
        </div>
      ))}
    </div>
  );
}
