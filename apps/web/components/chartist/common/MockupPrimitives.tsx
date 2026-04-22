// Primitive blocks that mirror the mockup's CSS class names so that once
// `globals.css` gains the matching rules, these render at full fidelity.
// Each block is presentational — data is always passed in via props.

import type { ReactNode } from "react";

// ---------------------------------------------------------------------------
// Breadcrumb
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Page Header
// ---------------------------------------------------------------------------
export function PageHeader({
  title,
  meta,
  subnav,
}: {
  title: string;
  meta?: string;
  subnav?: { label: string; active?: boolean }[];
}) {
  return (
    <div className="page-header flex items-end justify-between mb-3 gap-3 flex-wrap">
      <div className="page-title-group">
        <h1 className="display text-[28px] leading-tight">{title}</h1>
        {meta && (
          <div className="page-meta text-[10.5px] uppercase tracking-widest text-[color:var(--muted)] mt-1">
            {meta}
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

// ---------------------------------------------------------------------------
// Summary Row — dense 6-card strip
// ---------------------------------------------------------------------------
export interface SummaryCell {
  label: string;
  value: string;
  delta?: string;
  tone?: "pos" | "neg" | "amber" | "neutral";
}

function toneColor(t?: SummaryCell["tone"]): string {
  if (t === "pos") return "var(--pos)";
  if (t === "neg") return "var(--neg)";
  if (t === "amber") return "var(--accent)";
  return "var(--fg-muted)";
}

export function SummaryRow({ cells }: { cells: SummaryCell[] }) {
  return (
    <div
      className="summary-row grid gap-px mb-3 border rounded-md overflow-hidden"
      style={{
        background: "var(--border)",
        borderColor: "var(--border)",
        gridTemplateColumns: `repeat(${Math.min(cells.length, 6)}, minmax(0, 1fr))`,
      }}
    >
      {cells.map((c) => (
        <div
          key={c.label}
          className="summary-card px-3 py-2.5"
          style={{ background: "var(--surface)" }}
        >
          <div className="label text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
            {c.label}
          </div>
          <div className="value mono text-[17px] mt-0.5 text-[color:var(--fg)]">
            {c.value}
          </div>
          {c.delta && (
            <div
              className="delta mono text-[10.5px] mt-0.5"
              style={{ color: toneColor(c.tone) }}
            >
              {c.delta}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Panel wrapper
// ---------------------------------------------------------------------------
export function Panel({
  title,
  subtitle,
  children,
  bodyPad = true,
  style,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  bodyPad?: boolean;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className="panel rounded-md border overflow-hidden mb-3"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border)",
        ...style,
      }}
    >
      <div
        className="panel-header flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-[14px]">{title}</h2>
        {subtitle && (
          <span className="muted text-[10px] text-[color:var(--fg-muted)]">
            {subtitle}
          </span>
        )}
      </div>
      <div className={`panel-body ${bodyPad ? "p-3" : "p-0"}`}>{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stub block — empty-state for mock-only sections
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// QuoteStrip
// ---------------------------------------------------------------------------
export function QuoteStrip({ quote, attr }: { quote: string; attr?: string }) {
  return (
    <div
      className="quote-strip border-l-2 px-4 py-3 mb-3 text-[13px] italic flex items-baseline gap-3 flex-wrap"
      style={{
        borderColor: "var(--accent)",
        background: "var(--surface-2)",
        color: "var(--fg-muted)",
      }}
    >
      <span>&ldquo;{quote}&rdquo;</span>
      {attr && <span className="attr text-[10.5px] not-italic">{attr}</span>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chip primitive
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Mini table <th>/<td> helpers
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Heatmap (mockup-compatible)
// ---------------------------------------------------------------------------
export interface HeatCellProps {
  v: string;
  h: number;
}

export function Heatmap({
  headers,
  rows,
  firstColWidth = "140px",
}: {
  headers: string[];
  rows: { name: string; cells: HeatCellProps[] }[];
  firstColWidth?: string;
}) {
  const cols = headers.length;
  return (
    <div
      className="heatmap"
      style={{
        display: "grid",
        gridTemplateColumns: `${firstColWidth} repeat(${cols - 1}, 1fr)`,
        gap: "1px",
        background: "var(--border)",
        border: "1px solid var(--border)",
        borderRadius: 6,
        overflow: "hidden",
      }}
    >
      {headers.map((h, i) => (
        <div
          key={h + i}
          className={`hm-head ${i === 0 ? "first" : ""}`}
          style={{
            background: "var(--bg)",
            padding: "6px 10px",
            fontSize: 10,
            textTransform: "uppercase",
            letterSpacing: "0.04em",
            color: "var(--muted)",
            fontWeight: 500,
            textAlign: i === 0 ? "left" : "center",
          }}
        >
          {h}
        </div>
      ))}
      {rows.map((r) => (
        <HmRow key={r.name} r={r} />
      ))}
    </div>
  );
}

function HmRow({ r }: { r: { name: string; cells: HeatCellProps[] } }) {
  return (
    <>
      <div
        className="hm-name"
        style={{
          background: "var(--surface)",
          padding: "5px 10px",
          fontSize: 11.5,
          fontWeight: 500,
          display: "flex",
          alignItems: "center",
        }}
      >
        {r.name}
      </div>
      {r.cells.map((c, i) => (
        <div key={i} className={`hm-cell h${c.h}`}>
          {c.v}
        </div>
      ))}
    </>
  );
}

// ---------------------------------------------------------------------------
// Cond-list: condition pass rate bars
// ---------------------------------------------------------------------------
export interface CondRow {
  icon: string;
  iconTone?: "pos" | "amber" | "neg";
  label: string;
  pct: number;
  labelRight: string;
  amber?: boolean;
}

export function CondList({ rows }: { rows: CondRow[] }) {
  return (
    <div className="cond-list flex flex-col gap-2">
      {rows.map((r, i) => {
        const checkBg =
          r.iconTone === "amber"
            ? "var(--accent-soft)"
            : r.iconTone === "neg"
              ? "var(--neg-soft)"
              : "var(--pos-soft)";
        const checkColor =
          r.iconTone === "amber"
            ? "var(--accent)"
            : r.iconTone === "neg"
              ? "var(--neg)"
              : "var(--pos)";
        return (
          <div
            key={i}
            className="cond-row flex items-center gap-2.5 text-[11.5px]"
          >
            <span
              className="cond-check inline-flex items-center justify-center w-5 h-5 rounded text-[11px] font-medium"
              style={{ background: checkBg, color: checkColor }}
            >
              {r.icon}
            </span>
            <span className="cond-label flex-1 text-[color:var(--fg)]">
              {r.label}
            </span>
            <div
              className="cond-bar w-24 h-2 rounded-full overflow-hidden"
              style={{ background: "var(--bg)" }}
            >
              <div
                className="cond-bar-fill h-full rounded-full"
                style={{
                  width: `${r.pct}%`,
                  background: r.amber ? "var(--accent)" : "var(--pos)",
                }}
              />
            </div>
            <span
              className="cond-pct mono text-[10.5px] text-[color:var(--fg-muted)]"
              style={{ minWidth: 36, textAlign: "right" }}
            >
              {r.labelRight}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Activity log
// ---------------------------------------------------------------------------
export interface LogItem {
  time: string;
  tag: string;
  tagClass: "buy" | "sell" | "alert" | "sys";
  sym?: string;
  msg: string;
}

export function ActivityLog({ items }: { items: LogItem[] }) {
  return (
    <div className="activity-log">
      {items.map((it, i) => (
        <div key={i} className="log-row">
          <span className="log-time">{it.time}</span>
          <span className={`log-tag ${it.tagClass}`}>{it.tag}</span>
          <span className="log-msg">
            {it.sym && <span className="sym">{it.sym}</span>}
            {it.msg}
          </span>
        </div>
      ))}
    </div>
  );
}
