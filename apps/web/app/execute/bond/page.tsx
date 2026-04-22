import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="채권" title="채권" meta="국채 · 회사채">
      <StubBlock icon="B" title="채권 투자" desc="국고채 금리, 회사채 스프레드, YTM 계산기." />
    </DensePage>
  );
}
