// Chip primitive — colored rounded label with tone variants.

import type { ReactNode } from "react";

export function Chip({
  children,
  tone,
  className = "",
}: {
  children: ReactNode;
  tone?: "pos" | "neg" | "amber" | "accent" | "neutral";
  className?: string;
}) {
  const base =
    "chip inline-flex items-center gap-1.5 px-2 py-[1px] rounded-full text-[10px] border";
  let style: React.CSSProperties = {
    borderColor: "var(--border)",
    color: "var(--fg-muted)",
    background: "var(--bg)",
  };
  if (tone === "pos")
    style = {
      background: "var(--pos-soft)",
      color: "var(--pos)",
      borderColor: "transparent",
    };
  else if (tone === "neg")
    style = {
      background: "var(--neg-soft)",
      color: "var(--neg)",
      borderColor: "transparent",
    };
  else if (tone === "amber" || tone === "accent")
    style = {
      background: "var(--accent-soft)",
      color: "var(--accent)",
      borderColor: "transparent",
    };
  return (
    <span className={`${base} ${className}`} style={style}>
      {children}
    </span>
  );
}
