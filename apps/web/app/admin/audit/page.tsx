import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Admin" current="감사 로그" title="감사 로그" meta="AUDIT TRAIL">
      <StubBlock icon="A" title="모든 민감 작업 기록" desc="주문, 전략 배포, 설정 변경, 관리자 토큰 사용 — 모두 타임라인으로." />
    </DensePage>
  );
}
