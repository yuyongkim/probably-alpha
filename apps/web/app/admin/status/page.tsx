// Admin · Status — live service + secrets + DB + RAG state.
import { fetchEnvelope } from "@/lib/api";
import type { AdminStatus } from "@/types/admin";
import { StatusCards } from "@/components/admin/StatusCards";
import { DensePage } from "@/components/shared/DensePage";

export const revalidate = 60;

export default async function AdminStatusPage() {
  const status = await fetchEnvelope<AdminStatus>("/api/v1/admin/status");
  const secrets = status.secrets_present;
  return (
    <DensePage tab="Admin" current="시스템 상태" title="시스템 상태" meta="HEALTH · UPTIME · LATENCY">
      <section className="mb-6">
        <h2 className="display text-base mb-2">Data store</h2>
        <StatusCards status={status} />
      </section>
      <section className="mb-6">
        <h2 className="display text-base mb-2">Secrets present</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {Object.entries(secrets).map(([k, v]) => (
            <div
              key={k}
              className="rounded-md border px-3 py-2"
              style={{
                background: "var(--surface)",
                borderColor: v ? "var(--pos)" : "var(--neg)",
              }}
            >
              <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">{k}</div>
              <div className="mono text-sm" style={{ color: v ? "var(--pos)" : "var(--neg)" }}>
                {v ? "present" : "missing"}
              </div>
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2 className="display text-base mb-2">Feature flags</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {Object.entries(status.feature_flags).map(([k, v]) => (
            <div
              key={k}
              className="rounded-md border px-3 py-2"
              style={{ background: "var(--surface)", borderColor: "var(--border)" }}
            >
              <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">{k}</div>
              <div className="mono text-sm">{v ? "on" : "off"}</div>
            </div>
          ))}
        </div>
      </section>
    </DensePage>
  );
}
