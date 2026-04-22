// QuoteStrip — editorial pull-quote / highlight band.
// Use sparingly; one per page max.
// Target ≤ 40 lines.

export interface QuoteStripProps {
  quote: string;
  attribution?: string;
  source?: string;
  accent?: boolean;
}

export function QuoteStrip({ quote, attribution, source, accent = false }: QuoteStripProps) {
  return (
    <figure
      className={[
        "border-l-2 pl-4 py-2 my-6",
        accent ? "border-[color:var(--accent)]" : "border-border",
      ].join(" ")}
    >
      <blockquote className="display text-xl leading-snug">
        &ldquo;{quote}&rdquo;
      </blockquote>
      {(attribution || source) && (
        <figcaption className="mt-2 text-xs text-[color:var(--fg-muted)]">
          {attribution && <span>{attribution}</span>}
          {attribution && source && <span className="px-1">·</span>}
          {source && <span className="italic">{source}</span>}
        </figcaption>
      )}
    </figure>
  );
}
