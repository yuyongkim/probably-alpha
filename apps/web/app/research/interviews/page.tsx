import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Research" current="Wizards 인터뷰" title="Market Wizards 인터뷰" meta="JACK SCHWAGER · 3부작">
      <StubBlock icon="W" title="원전 인터뷰 아카이브" desc="Market Wizards / New Market Wizards / Stock Market Wizards 전체 인터뷰 인덱스 + RAG. 각 위저드의 매매 조건 원문 인용." chips={["Company_Credit 흡수"]} />
    </DensePage>
  );
}
