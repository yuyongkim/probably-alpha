// DensePage — mockup-style breadcrumb + page-header wrapper.
// Renders `.breadcrumb` + `.page-header` exactly as the integration mockup.
import type { ReactNode } from "react";

interface Props {
  tab: string;
  current: string;
  title: string;
  meta?: string;
  subNav?: { label: string; active?: boolean }[];
  children: ReactNode;
}

export function DensePage({ tab, current, title, meta, subNav, children }: Props) {
  return (
    <div>
      <div className="breadcrumb">
        {tab} <span className="sep">/</span>{" "}
        <span className="current">{current}</span>
      </div>
      <div className="page-header">
        <div className="page-title-group">
          <h1>{title}</h1>
          {meta ? <div className="page-meta">{meta}</div> : null}
        </div>
        {subNav && subNav.length > 0 ? (
          <div className="sub-nav">
            {subNav.map((n) => (
              <span
                key={n.label}
                className={`sub-nav-link${n.active ? " active" : ""}`}
              >
                {n.label}
              </span>
            ))}
          </div>
        ) : null}
      </div>
      {children}
    </div>
  );
}
