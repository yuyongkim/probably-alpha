// ROADMAP: KIS 선물옵션 TR (KOSPI200 선물/옵션, 상품선물) 미연결.
//          Execute API 의 /quote 는 market="J" (국내주식) 만 지원.
import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage
      tab="Execute"
      current="선물옵션"
      title="선물옵션"
      meta="KOSPI200 · 상품선물 · 주식선물"
    >
      <StubBlock
        icon="F"
        title="파생상품 트레이딩 — KIS 선옵 TR 미연결"
        desc="KOSPI200 선물/옵션, 상품선물, 주식선물 전용 TR 필요. 현 Execute API 는 주식만 지원."
        chips={["ROADMAP", "C: KIS TR 필요"]}
      />
    </DensePage>
  );
}
