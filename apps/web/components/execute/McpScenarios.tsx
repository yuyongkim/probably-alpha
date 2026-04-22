// McpScenarios — 12-scenario table for MCP trading template patterns.
import type { Scenario } from "@/types/execute";

function tone(s: "pos" | "neg" | "amber" | "default"): string {
  return s === "default" ? "" : ` ${s}`;
}

export function McpScenarios({ rows }: { rows: Scenario[] }) {
  return (
    <table className="mini">
      <thead>
        <tr><th>Scenario</th><th>트리거</th><th>Action</th><th>Safety</th></tr>
      </thead>
      <tbody>
        {rows.map((s) => (
          <tr key={s.name}>
            <td><strong>{s.name}</strong></td>
            <td>{s.trigger}</td>
            <td><span className={`chip${tone(s.actionTone)}`}>{s.action}</span></td>
            <td><span className={`chip${tone(s.safetyTone)}`}>{s.safety}</span></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
