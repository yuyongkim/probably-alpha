import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="선물옵션" title="선물옵션" meta="KOSPI200 · 상품선물 · CME">
      <StubBlock icon="F" title="파생상품 트레이딩" desc="KOSPI200 선물/옵션, 상품선물, 주식선물, 해외선물 — 전부 KIS로." />
    </DensePage>
  );
}
