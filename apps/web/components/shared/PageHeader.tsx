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
}

export function PageHeader({ crumbs, title, meta, subNav }: Props) {
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
