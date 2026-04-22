import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="주문 / 체결" title="주문 / 체결" meta="미체결 · 체결내역 · 주문오류">
      <StubBlock icon="O" title="주문 관리 콘솔" desc="신규 주문, 미체결 정정/취소, 당일 체결내역, 주문 오류 리트라이." />
    </DensePage>
  );
}
