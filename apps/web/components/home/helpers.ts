// Formatting + color helpers for the home dashboard.

export function toneColor(tone?: string): string {
  if (tone === "pos") return "var(--pos)";
  if (tone === "neg") return "var(--neg)";
  return "var(--fg-muted)";
}

export function pctColor(v: number | null | undefined): string {
  if (v == null) return "var(--fg-muted)";
  return v >= 0 ? "var(--pos)" : "var(--neg)";
}

// Strip UTF-16 lone surrogates that slip through from Python's
// surrogateescape codec (ingestion pipeline bug we haven't fully fixed).
// Without this Korean names render as black diamonds / question marks.
export function cleanSurrogates(s: string | null | undefined): string {
  if (!s) return "";
  return s.replace(/[\uD800-\uDFFF]/g, "");
}
