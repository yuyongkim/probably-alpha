import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="해외 선물옵션" title="해외 선물옵션" meta="CME · EUREX · HKEX">
      <StubBlock icon="F°" title="CME 원유 · 금 · S&P500 선물" desc="해외 선물옵션 API. 기본 헤지/투기 전략 지원." />
    </DensePage>
  );
}
