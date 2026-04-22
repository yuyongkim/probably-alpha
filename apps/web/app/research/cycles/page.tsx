import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards } from "@/components/shared/SummaryCards";
import { StubBlock } from "@/components/execute/StubBlock";
import { cyclesKpis } from "@/lib/research/mockData";

export default function Page() {
  return (
    <DensePage tab="Research" current="시장 사이클 사례" title="시장 사이클 아카이브" meta="과거 BUBBLE · CRASH · RECOVERY · 교훈">
      <SummaryCards cells={cyclesKpis} />
      <div style={{ marginTop: 14 }}>
        <StubBlock icon="H" title="과거 사이클 vs 현재 매칭" desc="현재 시장 패턴과 유사한 과거 구간 자동 매칭 (가격/밸류/금리/센티먼트 기준). 이후 경로 확률." />
      </div>
    </DensePage>
  );
}
