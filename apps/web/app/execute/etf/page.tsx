import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="ETF / ETN" title="ETF / ETN" meta="국내 · 해외">
      <StubBlock icon="E" title="ETF 포트폴리오" desc="테마 ETF 스크리닝, NAV 괴리율, 추종오차 추적." />
    </DensePage>
  );
}
