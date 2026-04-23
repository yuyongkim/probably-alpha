// EmptyState — "데이터 없음" placeholder used across Research/Admin pages.
// Target ≤ 40 lines.
interface Props {
  title: string;
  note?: string;
  hint?: string;
  variant?: "default" | "warn";
}

export function EmptyState({ title, note, hint, variant = "default" }: Props) {
  const accent =
    variant === "warn"
      ? "var(--neg, #bc4b51)"
      : "var(--accent, #1a1a1a)";
  return (
    <div
      className="p-6 rounded-md border border-dashed"
      style={{ borderColor: "var(--border)", background: "var(--surface)" }}
    >
      <div
        className="text-[10px] uppercase tracking-widest mb-2"
        style={{ color: accent }}
      >
        {variant === "warn" ? "Attention" : "No data yet"}
      </div>
      <div className="display text-base mb-1">{title}</div>
      {note ? (
        <div className="text-xs text-[color:var(--fg-muted)]">{note}</div>
      ) : null}
      {hint ? (
        <div className="mt-3 text-[11px] mono text-[color:var(--fg-muted)]">
          {hint}
        </div>
      ) : null}
    </div>
  );
}
