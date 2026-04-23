import { DensePage } from "@/components/shared/DensePage";
import { KRReportsPanel } from "@/components/research/KRReportsPanel";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="한국 증권사 리포트"
      title="국내 증권사 리포트 메타분석"
      meta="NAVER 리서치 · 종목/산업/시장/탐방/경제"
    >
      <KRReportsPanel />
    </DensePage>
  );
}
