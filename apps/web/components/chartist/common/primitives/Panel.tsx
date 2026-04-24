// Panel wrapper — titled card with header + body.

import type { ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  children,
  bodyPad = true,
  style,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  bodyPad?: boolean;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className="panel rounded-md border overflow-hidden mb-3"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
        ...style,
      }}
    >
      <div
        className="panel-header flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-[14px]">{title}</h2>
        {subtitle && (
          <span className="muted text-[10px] text-[color:var(--fg-muted)]">
            {subtitle}
          </span>
        )}
      </div>
      <div className={`panel-body ${bodyPad ? "p-3" : "p-0"}`}>{children}</div>
    </div>
  );
}
