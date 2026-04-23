import { DensePage } from "@/components/shared/DensePage";
import { ReviewPanel } from "@/components/research/ReviewPanel";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="주간/월간 리뷰"
      title="주간 / 월간 시장 리뷰"
      meta="ON-DEMAND · 기존 스캔/매크로 집계"
    >
      <ReviewPanel />
    </DensePage>
  );
}
