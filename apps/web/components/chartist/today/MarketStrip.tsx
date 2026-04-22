// MarketStrip — 8-cell index/yields ticker modeled on mockup `.market-strip`.
import type { MarketIndex, Tone } from "@/types/chartist";

interface Props {
  items: MarketIndex[];
}

function toneClass(tone: Tone): string {
  if (tone === "pos") return "text-[color:var(--pos)]";
  if (tone === "neg") return "text-[color:var(--neg)]";
  return "text-[color:var(--neutral)]";
}

export function MarketStrip({ items }: Props) {
  return (
    <div
      className="grid grid-cols-4 md:grid-cols-8 rounded-md overflow-hidden mb-3 border"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
      }}
    >
      {items.map((c, i) => (
        <div
          key={c.label}
          className="flex flex-col gap-[2px] px-3 py-2"
          style={{
            borderRight:
              i === items.length - 1 ? "none" : "1px solid var(--border)",
          }}
        >
          <span className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)] font-medium">
            {c.label}
          </span>
          <span className="mono text-[13px] font-medium">{c.value}</span>
          <span className={`mono text-[10.5px] font-medium ${toneClass(c.tone)}`}>
            {c.delta}
          </span>
        </div>
      ))}
    </div>
  );
}
