// Research · Buffett Letters — Berkshire letters + companion works.
import { fetchEnvelope } from "@/lib/api";
import type { BuffettIndex } from "@/types/research";
import { BuffettTimeline } from "@/components/research/BuffettTimeline";
import { BuffettSearch } from "@/components/research/BuffettSearch";
import { DensePage } from "@/components/shared/DensePage";

export const revalidate = 300;

export default async function BuffettLettersPage() {
  const idx = await fetchEnvelope<BuffettIndex>("/api/v1/research/buffett/index");
  return (
    <DensePage tab="Research" current="버핏 서한 21년" title="Berkshire Shareholder Letters" meta={`1977-2024 · ${idx.total_chunks.toLocaleString()} INDEXED CHUNKS`}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section>
          <h2 className="display text-lg mb-2">Works</h2>
          <BuffettTimeline index={idx} />
        </section>
        <section>
          <h2 className="display text-lg mb-2">Search</h2>
          <BuffettSearch />
        </section>
      </div>
    </DensePage>
  );
}
