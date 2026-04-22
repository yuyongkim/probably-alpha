import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Research" current="뉴스 / 리서치" title="뉴스 자동 분석" meta="SENTIMENT · IMPACT">
      <StubBlock icon="N" title="뉴스 감성 분석" desc="보유 종목/관심 종목 뉴스 자동 수집, 감성/중요도 스코어링." />
    </DensePage>
  );
}
