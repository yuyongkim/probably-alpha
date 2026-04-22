// Research · Knowledge Base — server fetches status, client search component.
import { fetchEnvelope } from "@/lib/api";
import type { KnowledgeStatus } from "@/types/research";
import { KnowledgeSearch } from "@/components/research/KnowledgeSearch";
import { DensePage } from "@/components/shared/DensePage";

export const revalidate = 300;

export default async function KnowledgePage() {
  let status: KnowledgeStatus | undefined;
  try {
    status = await fetchEnvelope<KnowledgeStatus>(
      "/api/v1/research/knowledge/status",
    );
  } catch {
    /* fall through */
  }
  const chunks = status?.chunks?.toLocaleString() ?? "?";
  const files = status?.files_indexed ?? "?";
  return (
    <DensePage tab="Research" current="Knowledge Base" title="Knowledge Base" meta={`TF-IDF · ${chunks} CHUNKS · ${files} FILES`}>
      <KnowledgeSearch initialStatus={status} />
    </DensePage>
  );
}
