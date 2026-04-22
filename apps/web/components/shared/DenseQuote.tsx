// DenseQuote — mockup `.quote-strip` italic pull-quote.

interface Props {
  quote: string;
  attribution?: string;
}

export function DenseQuote({ quote, attribution }: Props) {
  return (
    <div className="quote-strip">
      {quote}
      {attribution ? <span className="attr">{attribution}</span> : null}
    </div>
  );
}
