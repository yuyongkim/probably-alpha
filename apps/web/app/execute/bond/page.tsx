// ROADMAP: KIS 채권 시세/주문 TR 미연결. apps/api/routers/execute/ 에는
//          현재 주식 quote/orderbook/investor/program + SSE 만 구현됨.
//          국고채/회사채 금리·스프레드 계산기는 별도 데이터 소스 필요.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="채권" title="채권" meta="국채 · 회사채">
      <StubBlock
        icon="B"
        title="채권 투자 — KIS 채권 TR 미구현"
        desc="국고채 금리/회사채 스프레드/YTM 계산 모두 KIS 채권 전용 TR 또는 외부 금리 데이터가 필요합니다. 현재 Execute API는 주식만 지원."
        chips={["ROADMAP", "C: 외부 데이터 필요"]}
      />
    </DensePage>
  );
}
