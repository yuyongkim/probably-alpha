// ActivityLog — timestamped event stream with color-coded tags.
// Tags: BUY · SELL · VCP · EPS · DART · BRK · SYS (see globals.css).
import type { LogEvent } from "@/types/chartist";

interface Props {
  items: LogEvent[];
}

function tagClass(tag: string): string {
  const t = tag.toUpperCase();
  if (t === "BUY") return "log-tag buy";
  if (t === "SELL") return "log-tag sell";
  if (t === "SYS") return "log-tag sys";
  // VCP · EPS · DART · BRK all share the amber "alert" tone.
  return "log-tag alert";
}

export function ActivityLog({ items }: Props) {
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">Activity Log</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          LIVE · last {items.length}
        </span>
      </div>
      <div className="activity-log">
        {items.map((e, i) => (
          <div key={`${e.time}-${i}`} className="log-row">
            <span className="log-time">{e.time}</span>
            <span className={tagClass(e.tag)}>{e.tag}</span>
            <span className="log-msg">
              {e.symbol && <span className="sym">{e.symbol}</span>}
              {e.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
