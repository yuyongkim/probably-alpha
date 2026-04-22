import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="보유 포지션" title="보유 포지션 전체" meta="7 POSITIONS · 국내 5 · 해외 2">
      <StubBlock icon="P" title="포지션 상세 테이블" desc="각 포지션별 진입가/손절/목표가 · 실시간 손익 · 리스크 익스포저 · 한 번에 청산 버튼." />
    </DensePage>
  );
}
