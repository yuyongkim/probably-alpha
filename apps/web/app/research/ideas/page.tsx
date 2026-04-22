import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Research" current="아이디어 랩" title="전략 아이디어 랩" meta="BRAINSTORM · PROTOTYPE">
      <StubBlock icon="I" title="전략 아이디어 개발" desc="Claude와 함께 새 전략 브레인스토밍 → 간이 백테스트 → 본 백테스트." />
    </DensePage>
  );
}
