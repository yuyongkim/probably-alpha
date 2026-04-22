// Admin · FDD — data quality rule violations at a glance.
import { fetchEnvelope } from "@/lib/api";
import type { FddResponse } from "@/types/admin";
import { DensePage } from "@/components/shared/DensePage";

export const revalidate = 120;

const SEVERITY_COLOR: Record<string, string> = {
  high: "var(--neg)",
  medium: "var(--accent)",
  low: "var(--fg-muted)",
};

export default async function FDDPage() {
  const data = await fetchEnvelope<FddResponse>("/api/v1/admin/fdd");
  return (
    <DensePage tab="Admin" current="FDD 알럿" title="FDD 알럿 관리" meta="DATA QUALITY RULES">
      <div className="panel">
        <div className="panel-header"><h2>규칙별 위반 카운트</h2><span className="muted">0 이 아니면 upstream 점검</span></div>
        <div className="panel-body p0">
          <table className="mini">
            <thead><tr><th>Rule</th><th>Description</th><th>Severity</th><th className="num">Count</th></tr></thead>
            <tbody>
              {data.rules.map((r) => (
                <tr key={r.rule}>
                  <td className="mono text-xs">{r.rule}</td>
                  <td className="text-xs">{r.description}</td>
                  <td className="mono text-xs" style={{ color: SEVERITY_COLOR[r.severity] ?? "var(--fg-muted)" }}>{r.severity}</td>
                  <td className="num mono" style={{ color: r.count > 0 ? "var(--neg)" : "var(--fg-muted)" }}>
                    {r.count.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </DensePage>
  );
}
