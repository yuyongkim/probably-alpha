// CompassPlaybook — sector playbook list driven by Compass regime.
import type { PlaybookEntry } from "@/types/macro";

export function CompassPlaybook({ entries }: { entries: PlaybookEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-sm" style={{ color: "var(--text-muted)" }}>규칙 없음</p>;
  }
  return (
    <ul style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {entries.map((p) => (
        <li key={p.sector} style={{ borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
          <div className="display" style={{ fontSize: 14 }}>{p.sector}</div>
          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{p.rationale}</div>
        </li>
      ))}
    </ul>
  );
}
