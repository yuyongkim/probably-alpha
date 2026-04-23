// ROADMAP: KIS 해외주식 TR (미국/일본/홍콩) 미연결. 현 Execute API 의
//          /quote 는 market 파라미터를 받지만 실제 구현은 market="J"
//          (국내) 경로에 고정. 해외는 별도 TR + 환전 API 필요.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage
      tab="Execute"
      current="해외주식"
      title="해외주식 (미국 · 일본 · 홍콩)"
      meta="KIS 해외주식 API"
    >
      <StubBlock
        icon="US"
        title="해외주식 통합 화면 — KIS 해외 TR 미연결"
        desc="미국 Mag7/S&P500, 일본 닛케이225, 홍콩 H지수 전용 TR + 환전 TR 필요. 시세/체결/주문 전 계층 신규 연결."
        chips={["ROADMAP", "C: KIS 해외 TR 필요"]}
      />
    </DensePage>
  );
}
