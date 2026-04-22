// Chartist · History — 선정 히스토리 (stub).
import {
  Breadcrumb,
  PageHeader,
  Stub,
} from "@/components/chartist/common/MockupPrimitives";

export const revalidate = 60;

export default function ChartistHistoryPage() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "선정 히스토리"]} />
      <PageHeader
        title="추천 종목 트래킹"
        meta="과거 선정 vs 실제 결과"
      />
      <Stub
        icon="H"
        title="선정 이후 수익률 추적"
        desc="일자별 선정 종목, 이후 5/20/60일 수익률, 승률 통계, 실패한 선정의 사유 분석."
      />
    </div>
  );
}
