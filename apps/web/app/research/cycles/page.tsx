import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { RagFilterSearch } from "@/components/research/RagFilterSearch";
import { cyclesKpis } from "@/lib/research/mockData";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="시장 사이클 사례"
      title="시장 사이클 아카이브"
      meta="SHILLER · MACKAY · LTCM · BUBBLE & CRASH"
    >
      <SummaryCards cells={cyclesKpis} />
      <div style={{ marginTop: 14 }}>
        <RagFilterSearch slug="cycles" initialQuery="bubble crash" />
      </div>
    </DensePage>
  );
}
