// Shared tone and mini-table class helpers used by multiple primitives.

export const MINI_TABLE_CLS =
  "mini w-full text-[11px] border-collapse";
export const MINI_TH =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b text-left";
export const MINI_TH_NUM =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b text-right";
export const MINI_TD = "py-1 px-2";
export const MINI_TD_NUM = "py-1 px-2 mono text-[11px] text-right tabular-nums";
export const MINI_ROW_BORDER = { borderBottom: "1px solid var(--border-soft)" };

export function toneColorNumber(v: number): string {
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

export function signed(v: number, digits = 2): string {
  return v > 0 ? `+${v.toFixed(digits)}` : v.toFixed(digits);
}

export function toneColor(
  t?: "pos" | "neg" | "amber" | "neutral",
): string {
  if (t === "pos") return "var(--pos)";
  if (t === "neg") return "var(--neg)";
  if (t === "amber") return "var(--accent)";
  return "var(--fg-muted)";
}
