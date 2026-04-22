import { DensePage } from "@/components/shared/DensePage";
import { StubBlock } from "@/components/execute/StubBlock";
export default function Page() {
  return (
    <DensePage tab="Research" current="주간/월간 리뷰" title="주간 / 월간 시장 리뷰" meta="AUTO-GENERATED · CLAUDE">
      <StubBlock icon="R" title="자동 리뷰 리포트" desc="금요일 장 마감 후 자동 생성: 주간 주도 섹터, 주도 종목, 매크로 이벤트, 다음주 일정. 월말엔 월간 리뷰." />
    </DensePage>
  );
}
