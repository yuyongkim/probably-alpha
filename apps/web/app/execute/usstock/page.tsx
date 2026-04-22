import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="해외주식" title="해외주식 (미국 · 일본 · 홍콩)" meta="KIS 해외주식 API">
      <StubBlock icon="US" title="해외주식 통합 화면" desc="미국 Mag7 + S&P500, 일본 닛케이225, 홍콩 H지수. 환전 포함 주문." />
    </DensePage>
  );
}
