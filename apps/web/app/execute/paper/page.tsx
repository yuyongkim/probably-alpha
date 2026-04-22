import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="모의투자" title="모의투자" meta="KIS Paper Account">
      <StubBlock icon="$" title="전략 실전 투입 전 검증" desc="모의계좌로 2-4주 실행 → 실계좌 전환." />
    </DensePage>
  );
}
