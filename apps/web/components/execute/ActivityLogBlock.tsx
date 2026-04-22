// ActivityLogBlock — renders mockup `.activity-log` block.
import type { LogEntry } from "@/types/execute";

export function ActivityLogBlock({ items }: { items: LogEntry[] }) {
  return (
    <div className="activity-log">
      {items.map((e, i) => (
        <div key={`${e.time}-${i}`} className="log-row">
          <span className="log-time">{e.time}</span>
          <span className={`log-tag ${e.tagClass}`}>{e.tag}</span>
          <span className="log-msg">
            {e.sym ? <span className="sym">{e.sym}</span> : null}
            {e.symLabel ? `${e.symLabel} ${e.msg}` : e.msg}
          </span>
        </div>
      ))}
    </div>
  );
}
