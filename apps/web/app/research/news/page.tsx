import { DensePage } from "@/components/shared/DensePage";
import { NewsPanel } from "@/components/research/NewsPanel";

export default function Page() {
  return (
    <DensePage
      tab="Research"
      current="뉴스 / 리서치"
      title="뉴스 자동 분석"
      meta="NAVER · 키워드 기반 감성 스코어링"
    >
      <NewsPanel />
    </DensePage>
  );
}
