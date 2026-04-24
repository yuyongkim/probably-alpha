// Activity log primitive — time-tagged message rows, styled via globals.css.

export interface LogItem {
  time: string;
  tag: string;
  tagClass: "buy" | "sell" | "alert" | "sys";
  sym?: string;
  msg: string;
}

export function ActivityLog({ items }: { items: LogItem[] }) {
  return (
    <div className="activity-log">
      {items.map((it, i) => (
        <div key={i} className="log-row">
          <span className="log-time">{it.time}</span>
          <span className={`log-tag ${it.tagClass}`}>{it.tag}</span>
          <span className="log-msg">
            {it.sym && <span className="sym">{it.sym}</span>}
            {it.msg}
          </span>
        </div>
      ))}
    </div>
  );
}
