// SafetyRailsList — mockup `.cond-list` with 10 safety rails.
import type { SafetyRail } from "@/types/execute";

export function SafetyRailsList({ rails }: { rails: SafetyRail[] }) {
  return (
    <div className="cond-list">
      {rails.map((r) => (
        <div key={r.idx} className="cond-row">
          <span className="cond-check">{r.idx}</span>
          <span className="cond-label">{r.label}</span>
          <div className="cond-bar">
            <div
              className="cond-bar-fill"
              style={{
                width: `${r.fill}%`,
                background: r.color === "amber" ? "var(--amber)" : r.color === "neg" ? "var(--neg)" : undefined,
              }}
            />
          </div>
          <span className="cond-pct">{r.pct}</span>
        </div>
      ))}
    </div>
  );
}
