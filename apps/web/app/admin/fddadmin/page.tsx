// Admin · FDD — data quality rule violations at a glance.
import { fetchEnvelopeSafe } from "@/lib/api";
import type { FddResponse } from "@/types/admin";
import { DensePage } from "@/components/shared/DensePage";

export const revalidate = 120;

const SEVERITY_COLOR: Record<string, string> = {
  high: "var(--neg)",
  medium: "var(--accent)",
  low: "var(--fg-muted)",
};

export default async function FDDPage() {
  // The FDD endpoint is optional — when it isn't wired up we render an empty
  // state instead of crashing the admin shell.
  const { data, error } = await fetchEnvelopeSafe<FddResponse>(
    "/api/v1/admin/fdd",
    { rules: [] },
  );
  return (
    <DensePage tab="Admin" current="FDD 알럿" title="FDD 알럿 관리" meta="DATA QUALITY RULES">
      <div className="panel">
        <div className="panel-header"><h2>규칙별 위반 카운트</h2><span className="muted">0 이 아니면 upstream 점검</span></div>
        <div className="panel-body p0">
          {data.rules.length === 0 ? (
            <div className="p-6 text-sm text-[color:var(--fg-muted)]">
              {error
                ? "FDD endpoint 미연결 — /api/v1/admin/fdd 가 등록되면 여기 표시됩니다."
                : "등록된 규칙이 없습니다."}
            </div>
          ) : (
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
          )}
        </div>
      </div>
    </DensePage>
  );
}
