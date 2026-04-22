import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Execute" current="Strategy Builder" title="비주얼 Strategy Builder" meta="80 지표 · 57 캔들스틱 패턴 · AND/OR">
      <StubBlock icon="⚒" title="드래그 앤 드롭 전략 설계" desc="코드 없이 진입/청산 조건 조합. 손절/익절/트레일링 스톱. YAML 양방향 변환으로 Backtester와 공유. 실시간 시그널 BUY/SELL/HOLD + 강도 0~1." chips={["KIS 흡수"]} />
    </DensePage>
  );
}
