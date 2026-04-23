// ROADMAP: 주문 발주/미체결/정정/취소 TR 미연결. 현재 Execute API 는
//          조회(quote/orderbook/investor/program) + SSE 스트림만 지원.
//          주문 TR 은 별도 계좌 권한 + 안전장치(safety rails) 설계 필요.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage
      tab="Execute"
      current="주문 / 체결"
      title="주문 / 체결"
      meta="미체결 · 체결내역 · 주문오류"
    >
      <StubBlock
        icon="O"
        title="주문 콘솔 — KIS 주문 TR 미연결"
        desc="신규 주문/정정/취소, 당일 체결내역, 미체결 리스트 모두 KIS 주문 TR + 안전장치(일일 한도/kill-switch) 추가 구현 필요."
        chips={["ROADMAP", "C: KIS 주문 TR 필요"]}
      />
    </DensePage>
  );
}
