// Breadcrumb trail primitive — mirrors mockup class names.

export function Breadcrumb({ trail }: { trail: string[] }) {
  return (
    <div className="breadcrumb text-[11px] text-[color:var(--fg-muted)] mb-2">
      {trail.map((t, i) => (
        <span key={i}>
          {i > 0 && <span className="sep mx-1.5 text-[color:var(--muted)]">/</span>}
          {i === trail.length - 1 ? (
            <span className="current text-[color:var(--fg)]">{t}</span>
          ) : (
            t
          )}
        </span>
      ))}
    </div>
  );
}
