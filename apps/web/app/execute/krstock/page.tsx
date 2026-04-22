import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="국내주식" title="국내주식" meta="KOSPI · KOSDAQ · KONEX">
      <StubBlock icon="KR" title="국내주식 전용 화면" desc="호가창, 체결강도, 프로그램매매, 공매도 잔고 — 전부 KIS에서." />
    </DensePage>
  );
}
