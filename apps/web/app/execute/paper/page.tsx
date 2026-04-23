// ROADMAP: KIS 모의계좌 연동 미구현. 모의계좌 token/주문 TR 별도 플로우 필요.
//          현재는 실계좌 OAuth 만 /api/v1/execute/overview 에서 노출.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="모의투자" title="모의투자" meta="KIS Paper Account">
      <StubBlock
        icon="$"
        title="모의투자 계좌 — KIS Paper 연동 미구현"
        desc="모의계좌는 별도 OAuth + 주문 TR 플로우 필요. 실계좌와 동일 UI 재사용 가능하나 credentials 분리 필요."
        chips={["ROADMAP", "C: KIS Paper TR 필요"]}
      />
    </DensePage>
  );
}
