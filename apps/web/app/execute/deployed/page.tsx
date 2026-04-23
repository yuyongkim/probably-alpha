// ROADMAP: 배포된 전략 목록/상태/일시정지 기능은 전용 백엔드 필요
//          (strategy deployment registry + scheduler + kill switch).
//          현재 Execute API 는 시세/SSE 만 노출, 전략 실행 엔진 미구축.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage
      tab="Execute"
      current="배포 전략"
      title="배포된 전략"
      meta="LIVE · PAPER · PAUSED"
    >
      <StubBlock
        icon="S"
        title="전략 자동 실행 — 배포/스케줄러 미구현"
        desc="전략 배포 레지스트리, 일일 신호 스케줄러, KIS 자동 주문 훅 모두 신규 백엔드 필요. Kill-switch/pause API 없음."
        chips={["ROADMAP", "B: 신규 백엔드"]}
      />
    </DensePage>
  );
}
