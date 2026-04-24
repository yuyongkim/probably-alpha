// QuoteStrip primitive — left-accented italic pull-quote.

export function QuoteStrip({ quote, attr }: { quote: string; attr?: string }) {
  return (
    <div
      className="quote-strip border-l-2 px-4 py-3 mb-3 text-[13px] italic flex items-baseline gap-3 flex-wrap"
      style={{
        borderColor: "var(--accent)",
        background: "var(--surface-2)",
        color: "var(--fg-muted)",
      }}
    >
      <span>&ldquo;{quote}&rdquo;</span>
      {attr && <span className="attr text-[10.5px] not-italic">{attr}</span>}
    </div>
  );
}
