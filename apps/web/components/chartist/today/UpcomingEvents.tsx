// UpcomingEvents — compact calendar table. 실적 + macro mixed.
import type { UpcomingEvent } from "@/types/chartist";

interface Props {
  items: UpcomingEvent[];
}

const TH =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b";

function chipClass(type: string): string {
  if (type.toLowerCase() === "macro") return "chip amber";
  return "chip";
}

export function UpcomingEvents({ items }: Props) {
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">Upcoming Events</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">Earnings · Macro</span>
      </div>
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              Date
            </th>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              Ticker / Event
            </th>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              Type
            </th>
            <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }}>
              ConsEPS
            </th>
            <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>
              Note
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((e, i) => (
            <tr
              key={`${e.date}-${i}`}
              style={{ borderBottom: "1px solid var(--border-soft)" }}
              className="hover:bg-[color:var(--surface-2)]"
            >
              <td className="py-1 px-2 mono text-[10.5px] text-[color:var(--fg-muted)]">
                {e.date}
              </td>
              <td className="py-1 px-2">{e.ticker_or_event}</td>
              <td className="py-1 px-2">
                <span className={chipClass(e.type)}>{e.type}</span>
              </td>
              <td className="py-1 px-2 mono text-[11px] text-right tabular-nums">
                {e.consensus_eps ?? "—"}
              </td>
              <td className="py-1 px-2 text-[color:var(--fg-muted)]">{e.note}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
