// Chartist · Debate — 6인 트레이더 토론 (stub).
import {
  Breadcrumb,
  PageHeader,
  Stub,
} from "@/components/chartist/common/MockupPrimitives";

export const revalidate = 60;

export default function ChartistDebatePage() {
  return (
    <div>
      <Breadcrumb trail={["Chartist", "트레이더 토론"]} />
      <PageHeader
        title="Trader Debate"
        meta="6명의 시선으로 동일 종목 분석"
      />
      <Stub
        icon="D"
        title="종목 하나, 여섯 관점"
        desc="Minervini / O'Neil / Darvas / Livermore / Zanger / Weinstein 각자의 룰로 같은 종목을 평가하고 결론 비교."
      />
    </div>
  );
}
