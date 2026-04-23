// PageHeader — breadcrumb + page title + meta + optional sub-nav.
// Mirrors mockup `.page-header` / `.breadcrumb`. Presentational only.

interface Crumb {
  label: string;
  current?: boolean;
}

interface SubNavItem {
  label: string;
  active?: boolean;
}

interface Props {
  crumbs: Crumb[];
  title: string;
  meta?: string;
  subNav?: SubNavItem[];
  /** Latest trading day covered by the data on this page (ISO YYYY-MM-DD). */
  asOf?: string;
  /** Optional reference "today" — when provided and asOf < today, renders a stale badge. */
  today?: string;
}

export function PageHeader({ crumbs, title, meta, subNav, asOf, today }: Props) {
  const stale = asOf && today && asOf < today;
  return (
    <>
      <div className="breadcrumb">
        {crumbs.map((c, i) => (
          <span key={`${c.label}-${i}`}>
            {i > 0 ? <span className="sep"> / </span> : null}
            <span className={c.current ? "current" : undefined}>{c.label}</span>
          </span>
        ))}
      </div>
      <div className="page-header">
        <div className="page-title-group">
          <h1>{title}</h1>
          {meta ? <div className="page-meta">{meta}</div> : null}
          {asOf ? (
            <div
              className="mt-1 text-[10.5px] mono"
              style={{ color: stale ? "var(--accent)" : "var(--fg-muted)" }}
            >
              as-of {asOf}
              {stale ? (
                <span
                  className="ml-2 px-1.5 py-[1px] rounded border text-[10px]"
                  style={{
                    borderColor: "var(--accent)",
                    color: "var(--accent)",
                    background: "var(--accent-soft)",
                  }}
                >
                  stale · today {today}
                </span>
              ) : null}
            </div>
          ) : null}
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
    </>
  );
}
