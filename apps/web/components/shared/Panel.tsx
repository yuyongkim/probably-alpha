// Panel — `.panel` + `.panel-header` + `.panel-body` composite from mockup.
import type { ReactNode } from "react";

interface Props {
  title?: string;
  muted?: string;
  children: ReactNode;
  bodyPadding?: "default" | "p0" | "tight";
  className?: string;
  style?: React.CSSProperties;
}

export function Panel({ title, muted, children, bodyPadding = "default", className, style }: Props) {
  const bodyClass =
    bodyPadding === "p0" ? "panel-body p0" : "panel-body";
  const bodyStyle = bodyPadding === "tight" ? { padding: 10 } : undefined;
  return (
    <div className={`panel ${className ?? ""}`.trim()} style={style}>
      {title || muted ? (
        <div className="panel-header">
          {title ? <h2>{title}</h2> : <span />}
          {muted ? <span className="muted">{muted}</span> : null}
        </div>
      ) : null}
      <div className={bodyClass} style={bodyStyle}>
        {children}
      </div>
    </div>
  );
}
