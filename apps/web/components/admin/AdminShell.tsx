// AdminShell — generic page wrapper for admin sections still awaiting a source.
import { fetchEnvelope } from "@/lib/api";
import { EmptyState } from "@/components/shared/EmptyState";

interface Shell { slug: string; title: string; note: string; data: unknown[]; }

export async function AdminShell({ slug }: { slug: string }) {
  let shell: Shell | null = null;
  try {
    shell = await fetchEnvelope<Shell>(`/api/v1/admin/shell/${slug}`);
  } catch {
    /* keep null */
  }
  return (
    <div>
      <h1 className="display text-3xl mb-1">{shell?.title ?? slug}</h1>
      <p className="text-sm text-[color:var(--fg-muted)] mb-6">{shell?.note ?? "대기 중"}</p>
      <EmptyState
        title="데이터 없음"
        note="이 페이지는 아직 shell 상태입니다."
        hint={`GET /api/v1/admin/shell/${slug}`}
      />
    </div>
  );
}
