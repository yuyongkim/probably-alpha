import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="배포 전략" title="배포된 전략" meta="LIVE · PAPER · PAUSED">
      <StubBlock icon="S" title="전략 자동 실행" desc="전략 한 번 배포하면 매일 신호 생성 → KIS 자동 주문. 일시정지/재개 원클릭." />
    </DensePage>
  );
}
