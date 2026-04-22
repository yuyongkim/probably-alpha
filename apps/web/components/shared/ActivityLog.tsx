// ActivityLog — mockup `.activity-log` rows. Already styled via globals.css.

export type LogTag = "sys" | "buy" | "sell" | "alert";

export interface LogEntry {
  time: string;
  tag: LogTag;
  tagLabel?: string; // override short tag text
  message: React.ReactNode;
}

export function ActivityLog({ entries }: { entries: LogEntry[] }) {
  return (
    <div className="activity-log">
      {entries.map((e, i) => (
        <div key={i} className="log-row">
          <span className="log-time">{e.time}</span>
          <span className={`log-tag ${e.tag}`}>
            {e.tagLabel ?? e.tag.toUpperCase()}
          </span>
          <span className="log-msg">{e.message}</span>
        </div>
      ))}
    </div>
  );
}
