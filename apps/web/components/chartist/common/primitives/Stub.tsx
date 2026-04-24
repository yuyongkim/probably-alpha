// Stub primitive — empty-state card for sections that are still mock-only.

export function Stub({
  icon,
  title,
  desc,
  chips,
}: {
  icon: string;
  title: string;
  desc: string;
  chips?: string[];
}) {
  return (
    <div
      className="stub rounded-md border p-6 flex flex-col items-center text-center gap-3"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="stub-icon display text-[40px] flex items-center justify-center w-14 h-14 rounded-full"
        style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
      >
        {icon}
      </div>
      <div className="stub-title display text-lg">{title}</div>
      <div className="stub-desc text-[12.5px] text-[color:var(--fg-muted)] max-w-[640px] leading-relaxed">
        {desc}
      </div>
      {chips && chips.length > 0 && (
        <div className="stub-chips flex flex-wrap gap-1.5 mt-1">
          {chips.map((c) => (
            <span
              key={c}
              className="chip inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10.5px] border"
              style={{
                borderColor: "var(--border)",
                color: "var(--fg-muted)",
                background: "var(--bg)",
              }}
            >
              {c}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
