// AllocationBars — mockup 3-column allocation bar charts (자산군/섹터/전략).
import type { AllocationBar } from "@/types/execute";

interface Props {
  heading: string;
  bars: AllocationBar[];
}

export function AllocationBars({ heading, bars }: Props) {
  return (
    <div>
      <div
        style={{
          fontSize: 10,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.05em",
          fontWeight: 500,
          marginBottom: 8,
        }}
      >
        {heading}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
        {bars.map((b) => (
          <div
            key={b.label}
            style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11 }}
          >
            <span style={{ width: 72, color: "var(--text-secondary)" }}>{b.label}</span>
            <div style={{ flex: 1, height: 14, background: "var(--bg)", borderRadius: 3 }}>
              <div
                style={{
                  width: `${b.pct}%`,
                  height: "100%",
                  background: b.color,
                  borderRadius: 3,
                }}
              />
            </div>
            <span
              className="mono tnum"
              style={{ width: 48, textAlign: "right", fontSize: 10.5 }}
            >
              {b.pctLabel}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
