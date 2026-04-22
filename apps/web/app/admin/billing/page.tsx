import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Admin" current="사용량" title="사용량 / 빌링" meta="B2B 준비">
      <StubBlock icon="B" title="API 호출량 · LLM 토큰 · 스토리지" desc="개인 사용 단계에선 모니터링만, B2B 전환 시 tenant별 청구." />
    </DensePage>
  );
}
