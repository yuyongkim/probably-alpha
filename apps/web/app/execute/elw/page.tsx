import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="ELW" title="ELW (주식워런트)" meta="콜/풋 · 기초자산">
      <StubBlock icon="W" title="ELW 시세 + 주문" desc="KIS ELW API. 기초자산별 콜/풋 스크리닝, 내재변동성 조회." />
    </DensePage>
  );
}
