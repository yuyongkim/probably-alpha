// PageHeader primitive — title + optional meta, sub-nav, and as-of pill.

export function PageHeader({
  title,
  meta,
  subnav,
  asOf,
  today,
}: {
  title: string;
  meta?: string;
  subnav?: { label: string; active?: boolean }[];
  /** Latest trading day covered by the data on this page (ISO YYYY-MM-DD). */
  asOf?: string;
  /** Optional override for "today" — pass the server date to avoid SSR drift. */
  today?: string;
}) {
  const stale = asOf && today && asOf < today;
  return (
    <div className="page-header flex items-end justify-between mb-3 gap-3 flex-wrap">
      <div className="page-title-group">
        <h1 className="display text-[28px] leading-tight">{title}</h1>
        {meta && (
          <div className="page-meta text-[10.5px] uppercase tracking-widest text-[color:var(--muted)] mt-1">
            {meta}
          </div>
        )}
        {asOf && (
          <div
            className="mt-1 flex items-baseline gap-2 text-[10.5px]"
            style={{ color: stale ? "var(--accent)" : "var(--fg-muted)" }}
          >
            <span className="mono">as-of {asOf}</span>
            {stale && (
              <span
                className="px-1.5 py-[1px] rounded border mono text-[10px]"
                style={{
                  borderColor: "var(--accent)",
                  color: "var(--accent)",
                  background: "var(--accent-soft)",
                }}
              >
                stale · today {today}
              </span>
            )}
          </div>
        )}
      </div>
      {subnav && subnav.length > 0 && (
        <div className="sub-nav flex flex-wrap gap-1">
          {subnav.map((s) => (
            <span
              key={s.label}
              className={`sub-nav-link px-2.5 py-1 text-[11px] rounded border ${
                s.active
                  ? "border-[color:var(--accent)] text-[color:var(--accent)] bg-[color:var(--accent-soft)]"
                  : "border-[color:var(--border)] text-[color:var(--fg-muted)]"
              }`}
            >
              {s.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
