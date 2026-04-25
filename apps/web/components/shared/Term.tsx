"use client";

import { useEffect, useId, useRef, useState } from "react";

import { glossary } from "@/lib/glossary";

interface Props {
  /** Glossary key. Resolved against `lib/glossary.ts`. If missing, the
   *  component degrades to plain text — the page never breaks. */
  k: string;
  /** Display text. Defaults to glossary entry label or the key itself. */
  children?: React.ReactNode;
  /** Inline | block — block renders as a heading-friendly term. */
  variant?: "inline" | "block";
}

/**
 * Inline glossary term with hover/tap tooltip.
 *
 * Visual: dotted underline + tiny ? glyph after the term. Hover or tap
 * opens a small popover with a 1-2 sentence Korean definition and
 * optional source attribution. Closes on outside click and on Escape.
 *
 * Accessibility: implemented as `<button type="button">` so keyboard +
 * touch work without extra wiring. aria-describedby ties the tooltip
 * panel to the trigger.
 */
export function Term({ k, children, variant = "inline" }: Props) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const ref = useRef<HTMLSpanElement>(null);
  const def = glossary[k];

  // Outside-click + Escape close.
  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  // No glossary entry → render plain text. Page never breaks.
  if (!def) {
    return <>{children ?? k}</>;
  }

  const label = def.label ?? k;

  return (
    <span ref={ref} className="relative inline-block">
      <button
        type="button"
        aria-describedby={open ? id : undefined}
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className="inline-flex items-baseline gap-[0.2em] cursor-help bg-transparent border-0 p-0 m-0 font-inherit"
        style={{
          color: "inherit",
          borderBottom: "1px dotted currentColor",
          opacity: 0.92,
        }}
      >
        <span>{children ?? label}</span>
        <span
          aria-hidden
          className="inline-flex items-center justify-center rounded-full text-[0.62em] font-semibold leading-none"
          style={{
            width: "1.2em",
            height: "1.2em",
            background: "var(--accent-soft)",
            color: "var(--accent)",
            transform: "translateY(-0.15em)",
            transition: "background 120ms ease",
          }}
        >
          ?
        </span>
      </button>

      {open && (
        <span
          id={id}
          role="tooltip"
          className="absolute z-50 left-0 top-full mt-2 w-72 max-w-[80vw] p-3 rounded-md text-[12px] leading-relaxed text-left"
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            color: "var(--fg)",
            boxShadow:
              "0 8px 24px -8px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.6)",
            // Defensive: tooltip should not inherit cursor:help
            cursor: "default",
            // Prevent layout shift on inline parent
            whiteSpace: "normal",
          }}
        >
          {def.label && (
            <span
              className="block font-medium mb-1.5 text-[12.5px]"
              style={{ color: "var(--fg)" }}
            >
              {def.label}
            </span>
          )}
          <span className="block" style={{ color: "var(--fg-muted)" }}>
            {def.body}
          </span>
          {def.source && (
            <span
              className="block mt-2 pt-1.5 text-[10.5px] mono"
              style={{
                color: "var(--muted)",
                borderTop: "1px solid var(--border-soft)",
              }}
            >
              출처 · {def.source}
            </span>
          )}
        </span>
      )}
    </span>
  );
}
