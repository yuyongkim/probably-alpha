// Admin · Pipeline — recent job log listings from runtime_logs/.
import { fetchEnvelope } from "@/lib/api";
import type { JobsResponse } from "@/types/admin";
import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";

export const revalidate = 60;

const kpis = [
  { label: "Active Jobs", value: "3", delta: "EOD · Macro · KIS sync", tone: "pos" as const },
  { label: "Success · 24h", value: "47 / 48", delta: "98%", tone: "pos" as const },
  { label: "Avg Duration", value: "2m 14s", delta: "EOD 파이프라인" },
  { label: "Queue", value: "0", delta: "대기 없음", tone: "pos" as const },
];

export default async function PipelinePage() {
  const data = await fetchEnvelope<JobsResponse>("/api/v1/admin/jobs?limit=30");
  return (
    <DensePage tab="Admin" current="파이프라인 Jobs" title="파이프라인 Job 모니터" meta="OPS · RUN HISTORY">
      <SummaryCards cells={kpis} />
      <p className="text-sm text-[color:var(--fg-muted)] mb-4">
        <code className="mono">{data.root}</code> — 최근 {data.jobs.length}개 실행 로그.
        {data.warning ? ` · ${data.warning}` : ""}
      </p>
      <ul className="space-y-2">
        {data.jobs.map((j) => (
          <li key={j.name}
              className="rounded-md border p-3"
              style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}>
            <div className="flex items-baseline justify-between">
              <div>
                <span className="text-[10px] uppercase tracking-widest mr-2 px-1.5 py-0.5 rounded"
                      style={{ background: "var(--surface-2)", color: "var(--accent)" }}>
                  {j.kind}
                </span>
                <span className="mono text-sm">{j.name}</span>
              </div>
              <div className="mono text-[11px]" style={{ color: "var(--text-muted)" }}>
                {j.modified_at} · {(j.size_bytes / 1024).toFixed(1)} KB
              </div>
            </div>
            {j.tail.length > 0 ? (
              <pre className="mt-2 text-[11px] mono leading-relaxed opacity-70 whitespace-pre-wrap">
                {j.tail.join("\n")}
              </pre>
            ) : null}
          </li>
        ))}
      </ul>
    </DensePage>
  );
}
