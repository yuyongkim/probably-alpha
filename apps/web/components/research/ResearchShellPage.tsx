// ResearchShellPage — generic page wrapper for sections without data yet.
import { fetchEnvelope } from "@/lib/api";
import { EmptyState } from "@/components/shared/EmptyState";
import type { ShellResponse } from "@/types/research";

export async function ResearchShellPage({ slug }: { slug: string }) {
  let shell: ShellResponse | null = null;
  try {
    shell = await fetchEnvelope<ShellResponse>(`/api/v1/research/shell/${slug}`);
  } catch {
    /* keep null */
  }
  const title = shell?.title ?? slug;
  const note = shell?.note ?? "데이터 소스 연결 대기";
  return (
    <div>
      <h1 className="display text-3xl mb-1">{title}</h1>
      <p className="text-sm text-[color:var(--fg-muted)] mb-6">{note}</p>
      <EmptyState
        title="데이터 없음"
        note="이 섹션은 shell 상태입니다. 데이터 소스 연결이 완료되면 이 화면이 풍부해집니다."
        hint={`GET /api/v1/research/shell/${slug}`}
      />
    </div>
  );
}
