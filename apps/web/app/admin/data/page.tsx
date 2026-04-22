// Admin · Data Health — per-adapter healthcheck.
import { fetchEnvelope } from "@/lib/api";
import type { DataHealth } from "@/types/admin";
import { DensePage } from "@/components/shared/DensePage";

export const revalidate = 60;

export default async function DataHealthPage() {
  const data = await fetchEnvelope<DataHealth>("/api/v1/admin/data_health");
  return (
    <DensePage tab="Admin" current="데이터 소스" title="데이터 소스 상태" meta="KIS · KIWOOM · DART · FRED · ECOS · EIA · EXIM · NAVER">
      <div className="panel">
        <div className="panel-header"><h2>어댑터별 헬스체크</h2><span className="muted">CONFIG · LATENCY · LAST ERROR</span></div>
        <div className="panel-body p0">
          <table className="mini">
            <thead><tr><th>Source</th><th>Status</th><th className="num">Latency</th><th>Note</th></tr></thead>
            <tbody>
              {data.adapters.map((a) => {
                const ok = a.ok === true;
                return (
                  <tr key={a.source_id}>
                    <td className="mono">{a.source_id}</td>
                    <td><span className={`chip${ok ? " pos" : " neg"}`}>{ok ? "OK" : a.configured === false ? "not configured" : "FAIL"}</span></td>
                    <td className="num mono">{a.latency_ms != null ? `${(a.latency_ms as number).toFixed(0)} ms` : "—"}</td>
                    <td className="text-xs" style={{ color: "var(--text-muted)" }}>{a.last_error || a.import_error || "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </DensePage>
  );
}
