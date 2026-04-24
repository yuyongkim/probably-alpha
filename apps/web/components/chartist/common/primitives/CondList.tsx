// CondList primitive — condition pass-rate bars with tone-aware icons.

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
