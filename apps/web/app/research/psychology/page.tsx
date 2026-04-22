import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Research" current="트레이딩 심리" title="Trading Psychology Library" meta="ELDER · DOUGLAS · KAHNEMAN · WILDER">
      <div className="quote-strip">&ldquo;The market is a device for transferring money from the impatient to the patient.&rdquo; <span className="attr">— Warren Buffett</span></div>
      <StubBlock icon="Ψ" title="편향 · 감정 · 규율" desc='Elder "Trading for a Living", Douglas "Trading in the Zone", Kahneman "Thinking Fast and Slow" 발췌 + 실제 내 매매일지 교차 매핑.' />
    </DensePage>
  );
}
