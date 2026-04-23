// Admin · Keys — API-key presence (never values).
// Derived from /api/v1/admin/status.secrets_present when a dedicated /keys
// endpoint is unavailable — the information surface is identical.
import { fetchEnvelopeSafe } from "@/lib/api";
import type { AdminStatus, KeysResponse } from "@/types/admin";
import { DensePage } from "@/components/shared/DensePage";

export const revalidate = 120;

export default async function KeysPage() {
  const direct = await fetchEnvelopeSafe<KeysResponse>(
    "/api/v1/admin/keys",
    { keys: [], shared_env_loaded: false },
  );
  let data: KeysResponse = direct.data;
  if (direct.error || data.keys.length === 0) {
    const status = await fetchEnvelopeSafe<AdminStatus>(
      "/api/v1/admin/status",
      {
        owner_id: "unknown",
        shared_env_loaded: false,
        secrets_present: {},
        feature_flags: {},
      },
    );
    data = {
      shared_env_loaded: status.data.shared_env_loaded,
      keys: Object.entries(status.data.secrets_present).map(([name, present]) => ({
        name,
        status: present ? "present" : "missing",
      })),
    };
  }
  return (
    <DensePage tab="Admin" current="API 키 관리" title="API 키 관리" meta="~/.ky-platform/shared.env">
      <p className="text-sm text-[color:var(--fg-muted)] mb-4">
        이름별 존재 여부만 표시합니다. 실제 값은 절대 API / 프론트로 흐르지 않습니다.
        shared.env 로드: <strong>{data.shared_env_loaded ? "yes" : "no"}</strong>.
      </p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
        {data.keys.map((k) => (
          <div
            key={k.name}
            className="rounded-md border px-3 py-2"
            style={{
              background: "var(--surface)",
              borderColor: k.status === "present" ? "var(--pos)" : "var(--border-soft)",
            }}
          >
            <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">{k.name}</div>
            <div className="mono text-sm"
                 style={{ color: k.status === "present" ? "var(--pos)" : "var(--fg-muted)" }}>
              {k.status}
            </div>
          </div>
        ))}
      </div>
    </DensePage>
  );
}
